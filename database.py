"""
Database-lag for Campus Café (SQLite, ingen ekstra pakker nødvendige).

Tabeller: brugere, indstillinger, opslag, likes, arrangementer, deltagere,
frokostmakkere, bestillinger, notifikationer og en simuleret e-mail-udbakke.
"""

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from werkzeug.security import generate_password_hash

import os

# Kan flyttes med miljøvariablen DATABASE_PATH (fx til en persistent disk på serveren)
DB_PATH = Path(os.environ.get("DATABASE_PATH", Path(__file__).parent / "campus_cafe.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS brugere (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    navn TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    uddannelse TEXT DEFAULT '',
    oprettet TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS indstillinger (
    bruger_id INTEGER PRIMARY KEY REFERENCES brugere(id) ON DELETE CASCADE,
    notifikationer INTEGER NOT NULL DEFAULT 1,
    kanal TEXT NOT NULL DEFAULT 'app',          -- 'app' eller 'email'
    notif_menu INTEGER NOT NULL DEFAULT 1,
    notif_tilbud INTEGER NOT NULL DEFAULT 1,
    notif_makker INTEGER NOT NULL DEFAULT 1,
    notif_events INTEGER NOT NULL DEFAULT 1,
    notif_social INTEGER NOT NULL DEFAULT 1,
    kost TEXT NOT NULL DEFAULT 'alt',           -- 'alt', 'vegetarisk', 'vegansk', 'halal'
    offentlig_profil INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS opslag (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bruger_id INTEGER NOT NULL REFERENCES brugere(id) ON DELETE CASCADE,
    tekst TEXT NOT NULL,
    oprettet TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS likes (
    opslag_id INTEGER NOT NULL REFERENCES opslag(id) ON DELETE CASCADE,
    bruger_id INTEGER NOT NULL REFERENCES brugere(id) ON DELETE CASCADE,
    PRIMARY KEY (opslag_id, bruger_id)
);

CREATE TABLE IF NOT EXISTS arrangementer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titel TEXT NOT NULL,
    beskrivelse TEXT NOT NULL,
    dato TEXT NOT NULL,
    tid TEXT NOT NULL,
    sted TEXT NOT NULL,
    billede TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS deltagere (
    arrangement_id INTEGER NOT NULL REFERENCES arrangementer(id) ON DELETE CASCADE,
    bruger_id INTEGER NOT NULL REFERENCES brugere(id) ON DELETE CASCADE,
    PRIMARY KEY (arrangement_id, bruger_id)
);

CREATE TABLE IF NOT EXISTS frokostmakkere (
    bruger_id INTEGER NOT NULL REFERENCES brugere(id) ON DELETE CASCADE,
    dato TEXT NOT NULL,
    tidspunkt TEXT NOT NULL,
    PRIMARY KEY (bruger_id, dato)
);

CREATE TABLE IF NOT EXISTS bestillinger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bruger_id INTEGER NOT NULL REFERENCES brugere(id) ON DELETE CASCADE,
    ret TEXT NOT NULL,
    pris INTEGER NOT NULL,
    dato TEXT NOT NULL,
    afhentning TEXT NOT NULL,
    oprettet TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notifikationer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bruger_id INTEGER NOT NULL REFERENCES brugere(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    tekst TEXT NOT NULL,
    laest INTEGER NOT NULL DEFAULT 0,
    oprettet TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bruger_id INTEGER NOT NULL REFERENCES brugere(id) ON DELETE CASCADE,
    emne TEXT NOT NULL,
    tekst TEXT NOT NULL,
    oprettet TEXT NOT NULL
);
"""


def get_db() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def init_db() -> None:
    """Opretter tabeller og lægger demodata ind første gang."""
    con = get_db()
    con.executescript(SCHEMA)
    # Migration: ældre databaser mangler dato-kolonnen på bestillinger
    kolonner = [r["name"] for r in con.execute("PRAGMA table_info(bestillinger)")]
    if "dato" not in kolonner:
        con.execute("ALTER TABLE bestillinger ADD COLUMN dato TEXT NOT NULL DEFAULT ''")
        con.execute("UPDATE bestillinger SET dato = substr(oprettet, 1, 10) WHERE dato = ''")
    if con.execute("SELECT COUNT(*) FROM brugere").fetchone()[0] == 0:
        _seed(con)
    con.commit()
    con.close()


def _seed(con: sqlite3.Connection) -> None:
    # Demo-brugere (kodeord står også i README). Kun til prototypen.
    brugere = [
        ("Sofie Jensen", "demo@iba.dk", "demo1234", "Markedsføringsøkonom"),
        ("Mads Nielsen", "mads@iba.dk", "demo1234", "Datamatiker"),
        ("Aisha Khan", "aisha@iba.dk", "demo1234", "Finansøkonom"),
        ("Jonas Berg", "jonas@iba.dk", "demo1234", "Multimediedesigner"),
    ]
    for navn, email, pw, udd in brugere:
        cur = con.execute(
            "INSERT INTO brugere (navn, email, password_hash, uddannelse, oprettet) VALUES (?,?,?,?,?)",
            (navn, email, generate_password_hash(pw), udd, now()),
        )
        con.execute("INSERT INTO indstillinger (bruger_id) VALUES (?)", (cur.lastrowid,))

    i_dag = date.today()
    opslag = [
        (2, "Nogen der vil spise kl. 12 i dag? Jeg sidder ved vinduet på 1. sal.", 3),
        (3, "Pastaen i dag var virkelig god. Anbefales!", 2),
        (4, "Vi er en gruppe multimediedesignere, der spiller kort efter frokost om fredagen. Alle er velkomne.", 1),
    ]
    for bruger_id, tekst, timer_siden in opslag:
        con.execute(
            "INSERT INTO opslag (bruger_id, tekst, oprettet) VALUES (?,?,?)",
            (bruger_id, tekst, (datetime.now() - timedelta(hours=timer_siden)).isoformat(timespec="seconds")),
        )
    con.executemany("INSERT INTO likes VALUES (?,?)", [(1, 3), (1, 4), (2, 2), (2, 4), (3, 2)])

    arrangementer = [
        (
            "Fredagsbar i kantinen",
            "Kom og hæng ud efter ugens sidste time. Musik, brætspil og billige drikkevarer.",
            (i_dag + timedelta(days=(4 - i_dag.weekday()) % 7)).isoformat(), "15:00", "Campus Café",
            "https://images.unsplash.com/photo-1511795409834-ef04bbd61622?w=900&q=80",
        ),
        (
            "Quizaften",
            "Hold på 2-5 personer dyster i alt fra popkultur til IBA-viden. Præmie til vinderholdet.",
            (i_dag + timedelta(days=6)).isoformat(), "17:00", "Campus Café",
            "https://images.unsplash.com/photo-1543269865-cbf427effbad?w=900&q=80",
        ),
        (
            "Fælles brunch for nye studerende",
            "Mød dine medstuderende på tværs af uddannelser over en lang brunch.",
            (i_dag + timedelta(days=10)).isoformat(), "10:00", "Campus Café",
            "https://images.unsplash.com/photo-1533089860892-a7c6f0a88666?w=900&q=80",
        ),
    ]
    con.executemany(
        "INSERT INTO arrangementer (titel, beskrivelse, dato, tid, sted, billede) VALUES (?,?,?,?,?,?)",
        arrangementer,
    )
    con.executemany("INSERT INTO deltagere VALUES (?,?)", [(1, 2), (1, 3), (1, 4), (2, 3), (3, 2), (3, 4)])

    con.executemany(
        "INSERT INTO frokostmakkere VALUES (?,?,?)",
        [(2, i_dag.isoformat(), "12:00"), (3, i_dag.isoformat(), "12:00"), (4, i_dag.isoformat(), "12:30")],
    )
