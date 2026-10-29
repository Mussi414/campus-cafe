# Rapport: Modernisering af Campus Café-appen

**Projekt:** Campus Café – kantine-app til IBA Erhvervsakademi Kolding
**Dato:** 28. oktober 2026
**Teknologi:** Python 3.13 + Flask, HTML/CSS/JavaScript

---

## 1. Formål

Den oprindelige app var én enkelt HTML-fil med emojis som "billeder", flad styling
og `alert()`-bokse som eneste interaktion. Opgaven var at gøre appen mere moderne,
fjerne emojis, tilføje rigtige billeder af maden og baggrundsbilleder, og bygge den
i Python, så den kan køres og videreudvikles i VS Code.

## 2. Fra én HTML-fil til et Python-projekt

| Før | Efter |
|---|---|
| 1 HTML-fil med indlejret CSS og JS | Flask-projekt med adskilte filer |
| Menu skrevet direkte i HTML | Menu defineret som data i Python (`MENU`-listen i `app.py`) |
| Ingen server | Flask-server med 3 API-endpoints |
| `alert()`-popups | Toast-beskeder nederst på skærmen |

Projektstruktur:

```
campus_cafe/
├── app.py              # Flask-server, menu-data, tilbud, åbningstider og API
├── requirements.txt    # Afhængigheder (flask)
├── README.md           # Kørselsvejledning
├── RAPPORT.md          # Denne rapport
├── templates/
│   └── index.html      # Jinja2-skabelon, der genereres fra Python-data
└── static/
    ├── style.css       # Alt design
    └── app.js          # Knapper, formular, mobilmenu og toast
```

## 3. Hvad er ændret i designet

### Fjernet
- Alle emojis (☕ 🍔 🥗 🍝 🔥 🤝 🍽️) i overskrifter, menu-kort og knapper.
- `alert()`-bokse ved klik.
- Den flade orange header-bjælke og den sorte navigationsbjælke.

### Tilføjet
- **Hero-sektion med baggrundsbillede** af et café-interiør, mørk gradient-overlay,
  stor overskrift, to call-to-action-knapper og tre nøgletal (retter i dag, ugens
  tilbud, åbningstid).
- **Rigtige madbilleder** på hvert menu-kort (burger, salat, pasta) fra Unsplash,
  med zoom-effekt ved hover og et lille tag ("Populær", "Vegetarisk", "Dagens ret").
- **Tilbudssektion med baggrundsbillede** af en sandwich bag et orange overlay og
  parallax-effekt (fast baggrund på desktop).
- **Sticky, gennemsigtig navigation** med sløret baggrund, logo-badge og
  hamburgermenu på mobil.
- **Frokostmakker-formular** med navn og tidspunkt i stedet for en enkelt knap.
- **Info-sektion** med åbningstider, adresse og betalingsinfo.
- **Toast-beskeder** som erstatning for `alert()`.
- **Google-fonten Inter**, afrundede kort, bløde skygger, hover-animationer og et
  samlet farvetema defineret som CSS-variabler (IBA-orange er bevaret som
  primærfarve).
- **Responsivt layout**: grid'et tilpasser sig automatisk, og navigationen bliver
  til en hamburgermenu under 680 px.
- Fallback-baggrundsfarver, så siden stadig ser pæn ud uden internetforbindelse
  (billederne hentes fra nettet).

## 4. Hvad Python-delen gør

`app.py` indeholder:

- `GET /` – renderer siden med menu, tilbud, åbningstider og dagens dato.
- `POST /api/bestil` – modtager et ret-id, gemmer bestillingen i hukommelsen og
  returnerer et bestillingsnummer.
- `POST /api/makker` – tilmelder en studerende som frokostmakker og returnerer
  antal tilmeldte. Afviser tomme navne med fejlkode 400.
- `GET /api/menu` – returnerer menuen som JSON (klar til f.eks. en mobilapp).

Data gemmes kun i hukommelsen, så det nulstilles ved genstart. Det er bevidst –
appen er stadig en prototype uden betaling, præcis som den oprindelige.

## 5. Sådan bruges appen

1. Åbn mappen `campus_cafe` i VS Code.
2. Kør `pip install -r requirements.txt` i terminalen.
3. Kør `python app.py`.
4. Åbn http://127.0.0.1:5000.
5. Klik **Vælg ret** på et menu-kort – en toast bekræfter bestillingen med nummer.
6. Scroll til **Find en frokostmakker**, skriv dit navn, vælg tidspunkt og tryk
   **Tilmeld mig**.
7. Menuen ændres ved at redigere `MENU`-listen i `app.py`; Flask genindlæser
   automatisk i debug-mode.

## 6. Test

- Siden er åbnet i browser og gennemgået visuelt (hero, menu-kort med billeder,
  tilbud, formular, info-sektion).
- De tre API-endpoints er testet med `curl`: bestilling returnerer nr. 1,
  tilmelding returnerer bekræftelse, tom tilmelding afvises korrekt.
- Alle seks billedlinks svarer med HTTP 200.

## 7. Opdatering: Billeder fra IBA Kolding

Stock-baggrundene er erstattet med rigtige fotos af IBA's bygning i Havneparken,
hentet fra iba.dk og gemt lokalt i `static/images/`:

| Fil | Bruges til | Kilde |
|---|---|---|
| `iba-aften.jpg` | Hero-baggrund (bygningen ved åen i aftenlys) | iba.dk/international/the-ibas-new-premises |
| `iba-bygning.jpg` | Baggrund bag ugens tilbud (bygningen i solskin) | iba.dk/international/the-ibas-new-premises |
| `iba-indendoers.jpg` | Foto over frokostmakker-sektionen (studerende på 6. sal) | iba.dk/international/the-ibas-new-premises |

Der findes ingen offentlige fotos af selve kantinen på iba.dk, så det indendørs
billede er fra bygningens fællesareal. Billederne ligger nu lokalt, så hero og
tilbud virker uden internet. Madbillederne på menu-kortene hentes stadig fra
Unsplash. Fotokredit til IBA er tilføjet i footeren.

## 8. Opdatering: Fra hjemmeside til social app

**Dato:** 29. oktober 2026

Appen er udvidet fra én side til en rigtig app med login, database og sociale
funktioner. Den kan installeres på telefonen som en app (PWA).

### Nyt i Python-delen
- **SQLite-database** (`database.py`) med brugere, indstillinger, opslag, likes,
  arrangementer, deltagere, frokostmakkere, bestillinger, notifikationer og en
  simuleret e-mail-udbakke. Oprettes automatisk med demodata.
- **Login og oprettelse** med hashede kodeord (werkzeug) og sessions.
  Funktioner, der kræver login, sender brugeren til login og tilbage igen.
- **Notifikations-motor** (`notify()` i `app.py`), der respekterer brugerens
  indstillinger: er notifikationer slået fra, sendes intet; er kanalen e-mail,
  lander beskeden i e-mail-udbakken i stedet for i appen; og hver type
  (menu, tilbud, frokostmakker, arrangementer, socialt) kan slås fra enkeltvis.
- **API-endpoints** til forudbestilling, opslag, likes, arrangementer og
  frokostgrupper.

### Nye sider
| Side | Indhold |
|---|---|
| Hjem | Personlig hilsen, dagens menu med kostmarkering, ugens plan, tilbud, teasers til det sociale, åbningstider. Forudbestilling med afhentningstid i en dialog. |
| Log ind / Opret profil | Login-kort på IBA-baggrund med skift mellem log ind og oprettelse. |
| Socialt | Frokostgrupper pr. tidspunkt med avatarer, feed med opslag og likes, arrangementer med tilmelding og deltagerantal. |
| Beskeder | Notifikationer i appen, eller sendte e-mails hvis det er valgt. |
| Profil | Avatar, uddannelse, statistik, mine arrangementer og bestillinger. Log ud. |
| Indstillinger | Hovedkontakt for notifikationer, valg mellem app og e-mail, kontakter pr. type, kostpræference (alt, vegetarisk, vegansk, halal), navn og synlighed i frokostgrupper. |

### Det sociale
- **Frokostmakker**: vælg et af fire tidspunkter og se, hvem der allerede spiser.
  Andre i gruppen får besked, når du melder dig.
- **Opslag**: skriv korte beskeder (op til 280 tegn) og giv likes. Forfatteren
  får besked ved et like.
- **Arrangementer**: fredagsbar, quizaften og brunch med tilmelding og
  bekræftelse.

### App-følelse
- **Bundmenu** på mobil (Hjem, Socialt, Beskeder, Profil, Mere) med prik ved
  ulæste beskeder. Topbar på desktop.
- **PWA**: manifest, app-ikon og service worker, så appen kan installeres fra
  browseren og viser en offline-side uden netværk.
- Toast-beskeder, flash-beskeder, dialog til bestilling, skifte-kontakter og
  valgkort i indstillinger.

### Test
Gennemført i browseren med demo-brugeren: login, tilmelding til arrangement
(app-notifikation modtaget), tilmelding til frokostgruppe kl. 12:00, skift til
e-mail-kanal i indstillinger, forudbestilling (landede i e-mail-udbakken som
forventet), profilside og mobilvisning med bundmenu.

## 9. Opdatering: Forudbestilling op til 7 dage frem

- På forsiden viser boksen **"Forudbestil op til 7 dage frem"** i dag og de næste
  7 dage med dagens ret og pris. Weekenden vises som lukket. Hver åben dag har
  en Forudbestil-knap, der åbner bestillingsdialogen med dagen forudvalgt.
- Dialogen for dagens menu har nu også en **dagvælger** (kun åbne dage) og
  afhentningstid.
- Bestillinger gemmes med **dato** i databasen. Ældre databaser opgraderes
  automatisk med den nye kolonne.
- API'et afviser datoer uden for de 7 dage og weekender.
- Profilen viser **kommende forudbestillinger** med dato, tid og en
  Annuller-knap, og tidligere bestillinger for sig.
- Bekræftelsen (i app eller på e-mail) nævner dag og tidspunkt, fx
  "står klar mandag 2/11 kl. 12:00".
- Teknisk rettelse: CSS og JavaScript får nu et versionsnummer i adressen, og
  service workeren henter altid fra netværket først, så ændringer slår igennem
  med det samme og cachen kun bruges offline.

Testet i browseren: forudbestilling af mandagens ret fra ugeplanen, visning på
profilen og annullering.

## 10. Forslag til næste skridt

- Rigtige push-notifikationer og e-mails (f.eks. via Web Push og en mailserver).
- Admin-side, hvor kantinen selv kan opdatere dagens menu.
- Egne fotos af kantinen og dens retter (spørg evt. kantinelederen).
- Rigtig betaling via MobilePay-integration.
