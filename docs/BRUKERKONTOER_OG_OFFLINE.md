# Brukerkontoer (SaaS) og offline-støtte for OPS Monitor

## Kom i gang (implementert)

### Lokalt (for testing)

1. **Installer avhengigheter** (fra prosjektrot):
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-ui.txt
   ```

2. **Start backend-API lokalt**:
   ```bash
   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```
   APIet bruker SQLite (`./ops_monitor.db`) som standard. Sett `OPS_JWT_SECRET` og evt. `DATABASE_URL` i `.env` om du vil teste mot Postgres.

3. **Start desktop-appen**:
   ```bash
   python main_window.py
   ```
   Ved første kjøring vises innloggingsskjermen. Bruk **«Registrer ny bedrift»** for å opprette organisasjon og admin-bruker, eller **Logg inn** med eksisterende konto.

4. **API-URL**: I appen: *Innstillinger → Konto / API* kan du sette base URL (standard `http://127.0.0.1:8000`).

5. **Offline**: Hvis API ikke er tilgjengelig ved oppstart, brukes siste cachet bruker (fra `~/.ops_monitor/`) så lenge du har token, og statuslinjen viser «Offline». **Logg ut** er tilgjengelig via høyreklikk-meny.

### Prod: GitHub + Vercel (Postgres)

1. **Push til GitHub**
   - Initialiser git i prosjektet om ikke gjort:
     ```bash
     git init
     git add .
     git commit -m \"Initial OPS Monitor with backend\"
     git remote add origin <din-github-url>
     git push -u origin main
     ```

2. **Opprett Vercel-prosjekt**
   - Koble Vercel til GitHub-repoet.
   - Velg repoet ditt.
   - **Root directory**: la den stå til rot på repoet (der `server.py` ligger).

3. **Miljøvariabler i Vercel**
   - Legg inn minst:
     - `OPS_JWT_SECRET` – en lang, hemmelig streng.
     - `DATABASE_URL` – Postgres-URL fra Vercel Postgres/Neon, f.eks.\
       `postgres://USER:PASSWORD@HOST:PORT/DBNAME`.

   Backend leser `DATABASE_URL` via `backend/database.py` og faller tilbake til SQLite hvis den ikke er satt.

4. **Deploy**
   - Vercel bruker `requirements.txt` og `server.py` automatisk for FastAPI-støtte.
   - Første deploy skjer når du kobler repoet; senere deploys skjer på hver push til hoved-branch (eller etter Vercel-oppsett).

5. **Bruk fra OPS Monitor**
   - Finn prod-URLen til APIet på Vercel, f.eks. `https://ops-monitor-api.vercel.app`.
   - Sett denne URLen inn i desktop-appen under *Innstillinger → Konto / API*.
   - Nå vil innlogging, brukeradministrasjon og (senere) layout-sync gå mot Postgres-basen på Vercel.

---

## 1. Appnavn

Appen heter **OPS Monitor**. Vindustittel og produktnavn er satt i koden (`APP_NAME`, velkomstskjerm).

---

## 2. Hva må til for brukerkontoer (SaaS-modell)?

Typisk flyt:

- **Bedrift** registrerer seg (e-post, bedriftsnavn, evt. antall brukerplasser).
- **Admin** for bedriften logger inn og kan:
  - Legge til / fjerne brukere (opp til bedriftens “seats”).
  - Rolle (f.eks. admin vs vanlig bruker).
- **Brukere** logger inn med e-post/passord (eller SSO) og får tilgang til sine dashboards/layouts.

### Komponenter du trenger

| Del | Ansvarsområde |
|-----|----------------|
| **Backend-API** | Registrering, innlogging, JWT/sesjoner, CRUD for brukere/org, evt. layout-sync. |
| **Database** | Lagring av organisasjoner, brukere, roller, (evt. layout per bruker/org). |
| **Auth** | Passord-hashing (bcrypt/argon2), JWT eller session cookies, evt. OAuth (Google/Microsoft). |
| **Desktop-klient (OPS Monitor)** | Innloggingsskjerm, lagring av token, sende token på alle API-kall; evt. lokal cache for offline. |

Modellen “én bedrift med X brukerkontoer” blir typisk:

- **organizations** (id, name, plan, seat_count, …)
- **users** (id, organization_id, email, password_hash, role, …)
- **sessions** eller **refresh_tokens** for innlogging

Admin-API: kun brukere med `role = admin` i sin org kan opprette/slette brukere i samme org.

---

## 3. Database og Vercel

**Vercel** er først og fremst vert for **frontend og serverløse funksjoner**. Databasen kobler du til via et **API** som kjører på Vercel (eller annen host), ikke direkte fra desktop-appen.

### Alternativer med Vercel

- **Vercel Postgres** (Neon under panseret)  
  - Opprett database i Vercel-dashboard, få connection string.  
  - Bruk i **Serverless Functions** eller **Next.js API Routes** som kjører på Vercel.  
  - Desktop-appen snakker **aldri** direkte med databasen, kun med HTTPS-APIet.

- **Ekstern database** (Supabase, PlanetScale, Neon, etc.)  
  - Samme idé: API på Vercel (Next.js/Express/serverless) som leser/skriver mot databasen.  
  - Desktop-klienten kaller bare `https://ditt-api.vercel.app/...`.

### Anbefalt kobling fra OPS Monitor (desktop)

- **Base URL:** `https://ditt-projekt.vercel.app/api` (eller eget domene som peker til Vercel).
- **Endepunkter:** f.eks.  
  `POST /auth/register`, `POST /auth/login`,  
  `GET/POST /users`, `GET/PATCH /me`,  
  evt. `GET/POST /layouts` for synkronisering av layout.
- **Sikkerhet:**  
  - HTTPS.  
  - JWT i header (`Authorization: Bearer <token>`) eller cookie.  
  - Rate limiting og validering på API.  
  - Passord kun på server (hash + salt), aldri lagre rene passord.

Så: **Du kobler ikke desktop-appen “til Vercel” direkte** – du kobler den til **et API som du hoster på Vercel**, og APIet kobler til databasen (Vercel Postgres eller annen).

---

## 4. Robust offline-støtte

For at appen skal fungere godt uten nett:

- **Lokal tilstand:**  
  Bruk f.eks. SQLite eller JSON-filer lokalt til:
  - cache av brukerinfo og evt. siste layout,
  - kø med endringer som skjedde mens bruker var offline (f.eks. “oppdater layout”, “endre innstillinger”).
- **Synkronisering når nett er tilbake:**  
  - Sjekk tilkobling (som du allerede har med online/offline-indikator).  
  - Når appen kommer online: send køede endringer til APIet i en definert rekkefølge.  
  - Hent oppdatert data fra API (f.eks. bruker/layout) og oppdater lokal cache.
- **Konflikthåndtering:**  
  - Enkel strategi: “sist skrev vinner” med tidsstempel, eller at visse endringer (f.eks. layout) kun tillates fra én klient.  
  - Mer avansert: versjonering (f.eks. `version` eller `updated_at`) og evt. merge eller konflikt-UI.

For **innlogging**:

- **Første gang / ved utløpt token:** Krev nett og innlogging.  
- **Etter innlogging:** Lagre token sikkert (f.eks. Qt Keychain / credential store), og bruk cached bruker/layout offline til neste sync.

Kort sagt: **offline = lokal cache + operasjonskø; online = sync mot API og database**. Database (Vercel Postgres eller annen) brukes kun av backend-APIet, ikke direkte av OPS Monitor.

---

## 5. Implementasjonsrekkefølge (forslag)

1. **Backend:**  
   API (f.eks. Next.js på Vercel) + Vercel Postgres: tabeller for org, users, sessions; endepunkter for register, login, brukeradmin.
2. **Desktop:**  
   Innloggingsskjerm, lagre JWT, kall API med token; ved 401 → redirect til innlogging.
3. **Offline:**  
   Lokal SQLite/JSON for cache og kø; sync-loggikk ved “online”-event; enkel konflikthåndtering (f.eks. sist skrev vinner).

Når du vil konkretisere (f.eks. skjema for innlogging i PySide6 eller eksempel på Next.js API + Vercel Postgres), kan vi ta ett steg av gangen (f.eks. “login-skjerm” eller “sync ved oppstart”).
