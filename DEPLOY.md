# Få Campus Café på et rigtigt https-domæne

Lige nu kører appen kun på din egen computer (http://127.0.0.1:5000). For at få
en adresse med https og uden IP-nummer skal appen ligge på en server på
internettet. Den nemmeste gratis løsning er **Render**, som giver https og et
domæne automatisk. Det tager ca. 10 minutter.

Resultat: `https://campus-cafe.onrender.com` (navnet vælger du selv).

## Trin 1: Læg koden på GitHub

Render henter koden fra GitHub. Hvis `campus_cafe` ikke allerede er et
GitHub-repo:

1. Opret et nyt, tomt repository på https://github.com/new (fx `campus-cafe`).
2. Kør i terminalen i VS Code (stå i mappen `campus_cafe`):

   ```bash
   git init
   git add .
   git commit -m "Campus Café app"
   git branch -M main
   git remote add origin https://github.com/DIT-BRUGERNAVN/campus-cafe.git
   git push -u origin main
   ```

`.gitignore` sørger for, at databasen og `__pycache__` ikke kommer med.

## Trin 2: Opret appen på Render

1. Gå til https://render.com og log ind med din GitHub-konto.
2. Vælg **New → Blueprint** og peg på dit repository. Render finder
   `render.yaml` og sætter alt op selv (Python, gunicorn, hemmelig nøgle).
   Alternativt: **New → Web Service**, vælg repoet og brug:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`
3. Tryk **Deploy**. Efter 1-2 minutter har du en adresse som
   `https://campus-cafe.onrender.com` med gyldigt https-certifikat.

Hver gang du pusher til GitHub, opdateres appen automatisk.

## Trin 3 (valgfrit): Eget domæne, fx campuscafe.dk

1. Køb domænet hos fx one.com, simply.com eller dk-hostmaster-forhandler.
2. I Render: **Settings → Custom Domains → Add**, skriv dit domæne.
3. Hos domæneudbyderen opretter du den DNS-post, Render viser
   (en CNAME til `campus-cafe.onrender.com`).
4. Render udsteder automatisk et gratis https-certifikat.

## Godt at vide

- **Gratis-planen sover** efter 15 minutters inaktivitet. Første besøg kan
  tage 30-60 sekunder. Betalt plan (ca. 7 USD/md.) fjerner det.
- **Databasen (SQLite)** ligger på serverens disk og nulstilles ved hver ny
  deploy på gratis-planen. Til en prototype er det fint (demodata gendannes).
  Til rigtig drift: tilføj en Render Disk og sæt miljøvariablen
  `DATABASE_PATH=/var/data/campus_cafe.db`, eller skift til Postgres.
- **SECRET_KEY** genereres af Render. Sætter du appen op manuelt, så tilføj en
  miljøvariabel `SECRET_KEY` med en lang tilfældig tekst.
- **Install som app** virker først rigtigt på https. Når appen ligger på
  Render, kan brugerne installere den fra browseren på telefonen.

## Alternativer til Render

| Tjeneste       | Gratis | https | Bemærkning                              |
|----------------|--------|-------|------------------------------------------|
| Render         | Ja     | Ja    | Nemmest, bruger `render.yaml`            |
| Railway        | Prøve  | Ja    | Bruger `Procfile`                        |
| Fly.io         | Delvis | Ja    | Kræver `fly launch` på kommandolinjen    |
| PythonAnywhere | Ja     | Ja    | Upload via web, ingen git nødvendigt     |

Alle fire kan bruge filerne i denne mappe uden ændringer.
