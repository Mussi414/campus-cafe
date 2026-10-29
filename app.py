"""
Campus Café - IBA Erhvervsakademi Kolding
Social kantine-app bygget med Flask (Python).

Start appen:
    python app.py
Åbn derefter http://127.0.0.1:5000 i din browser.
Demo-login står på login-siden og i README.md.
"""

from datetime import date, datetime, timedelta
from functools import wraps

from flask import (Flask, abort, flash, g, jsonify, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db, init_db, now

import os

app = Flask(__name__)
# På en rigtig server sættes SECRET_KEY som miljøvariabel (se DEPLOY.md)
app.secret_key = os.environ.get("SECRET_KEY", "campus-cafe-prototype-skift-mig")
if os.environ.get("RENDER") or os.environ.get("PRODUCTION"):
    app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
init_db()  # opretter databasen og demodata første gang

# ---------------------------------------------------------------------------
# Statisk data (menu, tilbud, åbningstider)
# ---------------------------------------------------------------------------

UGEDAGE = ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag", "Lørdag", "Søndag"]

MENU = [
    {
        "id": 1,
        "navn": "Burger med pommes frites",
        "beskrivelse": "Saftig burger i briochebolle, serveret med sprøde pommes frites og aioli.",
        "pris": 65,
        "tag": "Populær",
        "kost": ["alt", "halal"],
        "billede": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800&q=80",
    },
    {
        "id": 2,
        "navn": "Frisk salat",
        "beskrivelse": "Sprød salat med sæsonens grøntsager, kerner og hjemmelavet dressing.",
        "pris": 45,
        "tag": "Vegansk",
        "kost": ["alt", "vegetarisk", "vegansk", "halal"],
        "billede": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=800&q=80",
    },
    {
        "id": 3,
        "navn": "Pasta med tomatsauce",
        "beskrivelse": "Al dente pasta vendt i en cremet tomatsauce med frisk basilikum og parmesan.",
        "pris": 55,
        "tag": "Vegetarisk",
        "kost": ["alt", "vegetarisk", "halal"],
        "billede": "https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?w=800&q=80",
    },
]

UGEMENU = {
    "Mandag": {"navn": "Kylling i karry med ris", "pris": 55},
    "Tirsdag": {"navn": "Lasagne med salat", "pris": 55},
    "Onsdag": {"navn": "Burger, salat eller pasta", "pris": 65},
    "Torsdag": {"navn": "Fiskefrikadeller med remoulade", "pris": 55},
    "Fredag": {"navn": "Pizza-buffet", "pris": 60},
}

FORUDBESTILLING_DAGE = 7  # hvor mange dage frem man kan forudbestille


def kommende_dage() -> list[dict]:
    """I dag og de næste 7 dage med ugedag, dagens ret og om kantinen har åbent."""
    dage = []
    for i in range(FORUDBESTILLING_DAGE + 1):
        d = date.today() + timedelta(days=i)
        ugedag = UGEDAGE[d.weekday()]
        label = "I dag" if i == 0 else ("I morgen" if i == 1 else f"{ugedag} {d.day}/{d.month}")
        dage.append({
            "iso": d.isoformat(), "label": label, "ugedag": ugedag,
            "aaben": d.weekday() < 5, "ret": UGEMENU.get(ugedag),
        })
    return dage

TILBUD = {
    "titel": "Sandwich + drik",
    "tekst": "Køb en sandwich og en valgfri drik for kun 45 kr. Gælder hele ugen fra kl. 11-14.",
    "pris": 45,
}

AABNINGSTIDER = [
    ("Mandag - torsdag", "07:30 - 15:00"),
    ("Fredag", "07:30 - 14:00"),
    ("Weekend", "Lukket"),
]

TIDSPUNKTER = ["11:30", "12:00", "12:30", "13:00"]


# ---------------------------------------------------------------------------
# Hjælpere
# ---------------------------------------------------------------------------

@app.before_request
def load_user():
    g.db = get_db()
    g.bruger = None
    g.indstillinger = None
    g.ulaeste = 0
    bruger_id = session.get("bruger_id")
    if bruger_id:
        g.bruger = g.db.execute("SELECT * FROM brugere WHERE id = ?", (bruger_id,)).fetchone()
        if g.bruger:
            g.indstillinger = g.db.execute(
                "SELECT * FROM indstillinger WHERE bruger_id = ?", (bruger_id,)
            ).fetchone()
            g.ulaeste = g.db.execute(
                "SELECT COUNT(*) FROM notifikationer WHERE bruger_id = ? AND laest = 0", (bruger_id,)
            ).fetchone()[0]
        else:
            session.clear()


@app.teardown_request
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def login_paakraevet(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if g.bruger is None:
            if request.path.startswith("/api/"):
                return jsonify({"ok": False, "besked": "Log ind for at gøre dette.", "login": True}), 401
            flash("Log ind for at bruge denne funktion.", "info")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return wrapper


def initialer(navn: str) -> str:
    dele = navn.split()
    return "".join(d[0] for d in dele[:2]).upper()


def relativ_tid(iso: str) -> str:
    t = datetime.fromisoformat(iso)
    diff = datetime.now() - t
    m = int(diff.total_seconds() // 60)
    if m < 1:
        return "lige nu"
    if m < 60:
        return f"{m} min. siden"
    h = m // 60
    if h < 24:
        return f"{h} t. siden"
    d = h // 24
    return "i går" if d == 1 else f"{d} dage siden"


def pæn_dato(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{UGEDAGE[d.weekday()][:3]}. {d.day}/{d.month}"


@app.context_processor
def static_versioning():
    """Giver CSS/JS et versionsnummer (filens ændringstid), så browser og
    service worker altid henter den nyeste udgave efter en ændring."""
    import os

    def static_url(filename: str) -> str:
        sti = os.path.join(app.static_folder, filename)
        v = int(os.path.getmtime(sti)) if os.path.exists(sti) else 0
        return url_for("static", filename=filename, v=v)

    return {"static_url": static_url}


app.jinja_env.filters["initialer"] = initialer
app.jinja_env.filters["relativ_tid"] = relativ_tid
app.jinja_env.filters["paen_dato"] = pæn_dato


def notify(bruger_id: int, type_: str, tekst: str, emne: str | None = None) -> None:
    """Sender en notifikation til en bruger - i appen eller som (simuleret) e-mail,
    afhængigt af brugerens indstillinger."""
    s = g.db.execute("SELECT * FROM indstillinger WHERE bruger_id = ?", (bruger_id,)).fetchone()
    if s is None or not s["notifikationer"]:
        return
    kategori = {
        "menu": s["notif_menu"], "tilbud": s["notif_tilbud"], "makker": s["notif_makker"],
        "event": s["notif_events"], "social": s["notif_social"], "bestilling": 1, "system": 1,
    }.get(type_, 1)
    if not kategori:
        return
    if s["kanal"] == "email":
        g.db.execute(
            "INSERT INTO emails (bruger_id, emne, tekst, oprettet) VALUES (?,?,?,?)",
            (bruger_id, emne or f"Campus Café: {type_.capitalize()}", tekst, now()),
        )
    else:
        g.db.execute(
            "INSERT INTO notifikationer (bruger_id, type, tekst, oprettet) VALUES (?,?,?,?)",
            (bruger_id, type_, tekst, now()),
        )


# ---------------------------------------------------------------------------
# Login / oprettelse
# ---------------------------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if g.bruger:
        return redirect(url_for("index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        pw = request.form.get("password", "")
        bruger = g.db.execute("SELECT * FROM brugere WHERE email = ?", (email,)).fetchone()
        if bruger and check_password_hash(bruger["password_hash"], pw):
            session["bruger_id"] = bruger["id"]
            flash(f"Velkommen tilbage, {bruger['navn'].split()[0]}!", "success")
            return redirect(request.args.get("next") or url_for("index"))
        flash("Forkert e-mail eller kodeord.", "error")
    return render_template("login.html", tab="login")


@app.route("/opret", methods=["GET", "POST"])
def opret():
    if g.bruger:
        return redirect(url_for("index"))
    if request.method == "POST":
        navn = request.form.get("navn", "").strip()
        email = request.form.get("email", "").strip().lower()
        pw = request.form.get("password", "")
        uddannelse = request.form.get("uddannelse", "").strip()
        if not navn or not email or len(pw) < 6:
            flash("Udfyld navn og e-mail, og vælg et kodeord på mindst 6 tegn.", "error")
        elif g.db.execute("SELECT 1 FROM brugere WHERE email = ?", (email,)).fetchone():
            flash("Der findes allerede en bruger med den e-mail.", "error")
        else:
            cur = g.db.execute(
                "INSERT INTO brugere (navn, email, password_hash, uddannelse, oprettet) VALUES (?,?,?,?,?)",
                (navn, email, generate_password_hash(pw), uddannelse, now()),
            )
            g.db.execute("INSERT INTO indstillinger (bruger_id) VALUES (?)", (cur.lastrowid,))
            g.db.execute(
                "INSERT INTO notifikationer (bruger_id, type, tekst, oprettet) VALUES (?,?,?,?)",
                (cur.lastrowid, "system",
                 f"Velkommen til Campus Café, {navn.split()[0]}! Find en frokostmakker eller se dagens menu.", now()),
            )
            g.db.commit()
            session["bruger_id"] = cur.lastrowid
            flash("Din profil er oprettet. Velkommen!", "success")
            return redirect(url_for("index"))
    return render_template("login.html", tab="opret")


@app.post("/logout")
def logout():
    session.clear()
    flash("Du er nu logget ud.", "info")
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Sider
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    i_dag = date.today()
    kost = g.indstillinger["kost"] if g.indstillinger else "alt"
    menu = [dict(r, passer=(kost in r["kost"])) for r in MENU]
    makkere_i_dag = g.db.execute(
        "SELECT COUNT(*) FROM frokostmakkere WHERE dato = ?", (i_dag.isoformat(),)
    ).fetchone()[0]
    naeste_event = g.db.execute(
        "SELECT a.*, (SELECT COUNT(*) FROM deltagere d WHERE d.arrangement_id = a.id) AS antal "
        "FROM arrangementer a WHERE dato >= ? ORDER BY dato LIMIT 1", (i_dag.isoformat(),)
    ).fetchone()
    return render_template(
        "index.html",
        menu=menu, ugemenu=UGEMENU, tilbud=TILBUD, aabningstider=AABNINGSTIDER,
        dage=kommende_dage(), tidspunkter=TIDSPUNKTER,
        dag=UGEDAGE[i_dag.weekday()], dato=i_dag.strftime("%d. %B %Y"),
        makkere_i_dag=makkere_i_dag, naeste_event=naeste_event, kost=kost,
    )


@app.route("/social")
def social():
    i_dag = date.today().isoformat()
    uid = g.bruger["id"] if g.bruger else 0
    opslag = g.db.execute(
        """SELECT o.*, b.navn, b.uddannelse,
                  (SELECT COUNT(*) FROM likes l WHERE l.opslag_id = o.id) AS likes,
                  EXISTS(SELECT 1 FROM likes l WHERE l.opslag_id = o.id AND l.bruger_id = ?) AS har_liket
           FROM opslag o JOIN brugere b ON b.id = o.bruger_id
           ORDER BY o.oprettet DESC LIMIT 30""", (uid,)
    ).fetchall()
    arrangementer = g.db.execute(
        """SELECT a.*, (SELECT COUNT(*) FROM deltagere d WHERE d.arrangement_id = a.id) AS antal,
                  EXISTS(SELECT 1 FROM deltagere d WHERE d.arrangement_id = a.id AND d.bruger_id = ?) AS deltager
           FROM arrangementer a WHERE dato >= ? ORDER BY dato""", (uid, i_dag)
    ).fetchall()
    grupper = []
    min_tid = None
    for tid in TIDSPUNKTER:
        navne = g.db.execute(
            """SELECT b.navn, b.id FROM frokostmakkere f JOIN brugere b ON b.id = f.bruger_id
               WHERE f.dato = ? AND f.tidspunkt = ? ORDER BY b.navn""", (i_dag, tid)
        ).fetchall()
        if any(n["id"] == uid for n in navne):
            min_tid = tid
        grupper.append({"tid": tid, "navne": navne})
    return render_template(
        "social.html", opslag=opslag, arrangementer=arrangementer, grupper=grupper, min_tid=min_tid
    )


@app.route("/notifikationer")
@login_paakraevet
def notifikationer():
    rows = g.db.execute(
        "SELECT * FROM notifikationer WHERE bruger_id = ? ORDER BY oprettet DESC LIMIT 50", (g.bruger["id"],)
    ).fetchall()
    g.db.execute("UPDATE notifikationer SET laest = 1 WHERE bruger_id = ?", (g.bruger["id"],))
    g.db.commit()
    emails = g.db.execute(
        "SELECT * FROM emails WHERE bruger_id = ? ORDER BY oprettet DESC LIMIT 20", (g.bruger["id"],)
    ).fetchall()
    return render_template("notifikationer.html", notifikationer=rows, emails=emails)


@app.route("/profil")
@login_paakraevet
def profil():
    uid = g.bruger["id"]
    i_dag = date.today().isoformat()
    kommende = g.db.execute(
        "SELECT * FROM bestillinger WHERE bruger_id = ? AND dato >= ? ORDER BY dato, afhentning", (uid, i_dag)
    ).fetchall()
    bestillinger = g.db.execute(
        "SELECT * FROM bestillinger WHERE bruger_id = ? AND dato < ? ORDER BY dato DESC LIMIT 10", (uid, i_dag)
    ).fetchall()
    mine_events = g.db.execute(
        "SELECT a.* FROM arrangementer a JOIN deltagere d ON d.arrangement_id = a.id "
        "WHERE d.bruger_id = ? AND a.dato >= ? ORDER BY a.dato", (uid, date.today().isoformat())
    ).fetchall()
    stats = {
        "opslag": g.db.execute("SELECT COUNT(*) FROM opslag WHERE bruger_id = ?", (uid,)).fetchone()[0],
        "events": len(mine_events),
        "bestillinger": g.db.execute("SELECT COUNT(*) FROM bestillinger WHERE bruger_id = ?", (uid,)).fetchone()[0],
    }
    return render_template("profil.html", bestillinger=bestillinger, kommende=kommende,
                           mine_events=mine_events, stats=stats)


@app.post("/api/bestilling/<int:bestilling_id>/annuller")
@login_paakraevet
def api_annuller_bestilling(bestilling_id):
    b = g.db.execute("SELECT * FROM bestillinger WHERE id=? AND bruger_id=?", (bestilling_id, g.bruger["id"])).fetchone()
    if b is None:
        abort(404)
    if b["dato"] < date.today().isoformat():
        return jsonify({"ok": False, "besked": "Bestillingen er allerede afhentet."}), 400
    g.db.execute("DELETE FROM bestillinger WHERE id=?", (bestilling_id,))
    g.db.commit()
    return jsonify({"ok": True, "besked": f"Bestilling nr. {bestilling_id} er annulleret."})


@app.route("/indstillinger", methods=["GET", "POST"])
@login_paakraevet
def indstillinger():
    uid = g.bruger["id"]
    if request.method == "POST":
        f = request.form
        on = lambda key: 1 if f.get(key) == "on" else 0  # noqa: E731
        kanal = "email" if f.get("kanal") == "email" else "app"
        g.db.execute(
            """UPDATE indstillinger SET notifikationer=?, kanal=?, notif_menu=?, notif_tilbud=?,
               notif_makker=?, notif_events=?, notif_social=?, kost=?, offentlig_profil=?
               WHERE bruger_id=?""",
            (on("notifikationer"), kanal, on("notif_menu"), on("notif_tilbud"), on("notif_makker"),
             on("notif_events"), on("notif_social"), f.get("kost", "alt"), on("offentlig_profil"), uid),
        )
        navn = f.get("navn", "").strip()
        uddannelse = f.get("uddannelse", "").strip()
        if navn:
            g.db.execute("UPDATE brugere SET navn=?, uddannelse=? WHERE id=?", (navn, uddannelse, uid))
        g.db.commit()
        flash("Dine indstillinger er gemt.", "success")
        return redirect(url_for("indstillinger"))
    return render_template("indstillinger.html")


# ---------------------------------------------------------------------------
# API (kaldes fra app.js)
# ---------------------------------------------------------------------------

@app.post("/api/bestil")
@login_paakraevet
def api_bestil():
    data = request.get_json(silent=True) or {}

    # Dato: i dag eller op til 7 dage frem, kun hverdage
    dato_iso = data.get("dato") or date.today().isoformat()
    dag = next((d for d in kommende_dage() if d["iso"] == dato_iso), None)
    if dag is None:
        return jsonify({"ok": False, "besked": f"Du kan forudbestille op til {FORUDBESTILLING_DAGE} dage frem."}), 400
    if not dag["aaben"]:
        return jsonify({"ok": False, "besked": "Kantinen har lukket i weekenden."}), 400

    # Retten: enten fra dagens menu (id) eller fra ugens plan (ugedag)
    if data.get("id") is not None:
        ret = next((r for r in MENU if r["id"] == data.get("id")), None)
    else:
        ret = dag["ret"]
    if ret is None:
        return jsonify({"ok": False, "besked": "Retten blev ikke fundet."}), 404

    afhentning = data.get("afhentning") if data.get("afhentning") in TIDSPUNKTER else "12:00"
    cur = g.db.execute(
        "INSERT INTO bestillinger (bruger_id, ret, pris, dato, afhentning, oprettet) VALUES (?,?,?,?,?,?)",
        (g.bruger["id"], ret["navn"], ret["pris"], dato_iso, afhentning, now()),
    )
    hvornaar = f"{dag['label'].lower()} kl. {afhentning}"
    notify(g.bruger["id"], "bestilling",
           f"Din forudbestilling nr. {cur.lastrowid} ({ret['navn']}) står klar {hvornaar}.",
           emne="Din forudbestilling er registreret")
    g.db.commit()
    return jsonify({"ok": True, "besked": f"Bestilling nr. {cur.lastrowid}: {ret['navn']} står klar {hvornaar}. "
                                          "Betaling sker ved afhentning (prototype)."})


@app.post("/api/opslag")
@login_paakraevet
def api_opslag():
    tekst = (request.get_json(silent=True) or {}).get("tekst", "").strip()
    if not tekst or len(tekst) > 280:
        return jsonify({"ok": False, "besked": "Skriv mellem 1 og 280 tegn."}), 400
    g.db.execute("INSERT INTO opslag (bruger_id, tekst, oprettet) VALUES (?,?,?)", (g.bruger["id"], tekst, now()))
    g.db.commit()
    return jsonify({"ok": True, "besked": "Dit opslag er delt."})


@app.post("/api/like/<int:opslag_id>")
@login_paakraevet
def api_like(opslag_id):
    uid = g.bruger["id"]
    opslag = g.db.execute("SELECT * FROM opslag WHERE id = ?", (opslag_id,)).fetchone()
    if opslag is None:
        abort(404)
    if g.db.execute("SELECT 1 FROM likes WHERE opslag_id=? AND bruger_id=?", (opslag_id, uid)).fetchone():
        g.db.execute("DELETE FROM likes WHERE opslag_id=? AND bruger_id=?", (opslag_id, uid))
        liket = False
    else:
        g.db.execute("INSERT INTO likes VALUES (?,?)", (opslag_id, uid))
        liket = True
        if opslag["bruger_id"] != uid:
            notify(opslag["bruger_id"], "social", f"{g.bruger['navn']} synes godt om dit opslag.")
    g.db.commit()
    antal = g.db.execute("SELECT COUNT(*) FROM likes WHERE opslag_id=?", (opslag_id,)).fetchone()[0]
    return jsonify({"ok": True, "liket": liket, "antal": antal})


@app.post("/api/event/<int:event_id>")
@login_paakraevet
def api_event(event_id):
    uid = g.bruger["id"]
    ev = g.db.execute("SELECT * FROM arrangementer WHERE id = ?", (event_id,)).fetchone()
    if ev is None:
        abort(404)
    if g.db.execute("SELECT 1 FROM deltagere WHERE arrangement_id=? AND bruger_id=?", (event_id, uid)).fetchone():
        g.db.execute("DELETE FROM deltagere WHERE arrangement_id=? AND bruger_id=?", (event_id, uid))
        deltager, besked = False, f"Du er afmeldt {ev['titel']}."
    else:
        g.db.execute("INSERT INTO deltagere VALUES (?,?)", (event_id, uid))
        deltager, besked = True, f"Du deltager i {ev['titel']} {pæn_dato(ev['dato'])} kl. {ev['tid']}."
        notify(uid, "event", f"Du er tilmeldt {ev['titel']} {pæn_dato(ev['dato'])} kl. {ev['tid']} i {ev['sted']}.",
               emne=f"Tilmelding: {ev['titel']}")
    g.db.commit()
    antal = g.db.execute("SELECT COUNT(*) FROM deltagere WHERE arrangement_id=?", (event_id,)).fetchone()[0]
    return jsonify({"ok": True, "deltager": deltager, "antal": antal, "besked": besked})


@app.post("/api/makker")
@login_paakraevet
def api_makker():
    uid = g.bruger["id"]
    tid = (request.get_json(silent=True) or {}).get("tidspunkt")
    i_dag = date.today().isoformat()
    eksisterende = g.db.execute(
        "SELECT tidspunkt FROM frokostmakkere WHERE bruger_id=? AND dato=?", (uid, i_dag)
    ).fetchone()
    if eksisterende and eksisterende["tidspunkt"] == tid:
        g.db.execute("DELETE FROM frokostmakkere WHERE bruger_id=? AND dato=?", (uid, i_dag))
        g.db.commit()
        return jsonify({"ok": True, "tilmeldt": False, "besked": "Du er afmeldt dagens frokostgruppe."})
    if tid not in TIDSPUNKTER:
        return jsonify({"ok": False, "besked": "Ugyldigt tidspunkt."}), 400
    g.db.execute("INSERT OR REPLACE INTO frokostmakkere VALUES (?,?,?)", (uid, i_dag, tid))
    andre = g.db.execute(
        "SELECT bruger_id FROM frokostmakkere WHERE dato=? AND tidspunkt=? AND bruger_id<>?", (i_dag, tid, uid)
    ).fetchall()
    for r in andre:
        notify(r["bruger_id"], "makker", f"{g.bruger['navn'].split()[0]} spiser også kl. {tid} i dag. I er nu {len(andre) + 1} i gruppen.")
    g.db.commit()
    besked = (f"Du spiser kl. {tid} sammen med {len(andre)} andre. Find bordet med skiltet 'Frokostmakkere'."
              if andre else f"Du er den første kl. {tid}. Vi giver besked, når andre melder sig.")
    return jsonify({"ok": True, "tilmeldt": True, "besked": besked})


@app.get("/api/menu")
def api_menu():
    return jsonify(MENU)


# ---------------------------------------------------------------------------
# PWA
# ---------------------------------------------------------------------------

@app.route("/manifest.json")
def manifest():
    return app.send_static_file("manifest.json")


@app.route("/sw.js")
def service_worker():
    resp = app.send_static_file("sw.js")
    resp.headers["Service-Worker-Allowed"] = "/"
    return resp


if __name__ == "__main__":
    # Lokalt: python app.py  ->  http://127.0.0.1:5000
    # På server bruges gunicorn (se Procfile), ikke denne udviklingsserver.
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
