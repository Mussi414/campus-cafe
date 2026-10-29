# Campus Café – IBA Kolding

Social kantine-app bygget i Python (Flask) med SQLite-database. Kan installeres
som app på telefonen (PWA).

## Sådan kører du appen i VS Code

1. Åbn mappen `campus_cafe` i VS Code (File → Open Folder).
2. Åbn terminalen (Ctrl + `) og installer Flask:

   ```bash
   pip install -r requirements.txt
   ```

3. Start appen:

   ```bash
   python app.py
   ```

4. Åbn http://127.0.0.1:5000 i din browser.

Databasen `campus_cafe.db` oprettes automatisk med demodata første gang.
Slet filen, hvis du vil starte forfra.

## Demo-login

| E-mail        | Kodeord  | Navn          |
|---------------|----------|---------------|
| demo@iba.dk   | demo1234 | Sofie Jensen  |
| mads@iba.dk   | demo1234 | Mads Nielsen  |
| aisha@iba.dk  | demo1234 | Aisha Khan    |
| jonas@iba.dk  | demo1234 | Jonas Berg    |

Du kan også oprette din egen profil under "Opret profil".

## Funktioner

- **Hjem** – dagens menu med billeder, ugens plan, tilbud og åbningstider.
  Retter markeres efter din kostpræference. Forudbestil dagens ret eller en
  ret fra ugeplanen op til 7 dage frem med afhentningstid.
- **Socialt** – frokostgrupper (vælg tidspunkt og se hvem der spiser med),
  opslag med likes og arrangementer med tilmelding.
- **Beskeder** – notifikationer i appen eller som e-mail (simuleret udbakke).
- **Profil** – dine arrangementer, kommende forudbestillinger (kan annulleres)
  og statistik.
- **Indstillinger** – slå notifikationer til/fra, vælg app eller e-mail,
  vælg hvilke typer du vil have, kostpræference og profiloplysninger.
- **Installer som app** – i Chrome/Edge: menuen → "Installer Campus Café".
  På iPhone: Del → "Føj til hjemmeskærm".

## Struktur

```
campus_cafe/
├── app.py               # Flask-server: sider, login, API, notifikationer
├── database.py          # SQLite-skema og demodata
├── requirements.txt
├── templates/
│   ├── base.html        # Fælles layout: topbar, bundmenu, toast
│   ├── index.html       # Hjem (menu, tilbud, teasers)
│   ├── login.html       # Log ind / opret profil
│   ├── social.html      # Frokostmakker, opslag, arrangementer
│   ├── notifikationer.html
│   ├── profil.html
│   └── indstillinger.html
└── static/
    ├── style.css        # Alt design
    ├── app.js           # Knapper, dialog, likes, service worker
    ├── manifest.json    # PWA-manifest
    ├── sw.js            # Service worker (installerbar + offline)
    ├── icon.svg         # App-ikon
    └── images/          # Fotos af IBA-bygningen
```

## Sådan ændrer du menuen

Rediger `MENU` og `UGEMENU` øverst i `app.py`. Flask genindlæser automatisk i
debug-mode. Arrangementer og brugere ligger i databasen (se `database.py`).
