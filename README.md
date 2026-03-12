## OPS Monitor

Desktop-app for vakt-/personellstatus med Excel-import (Microsoft Forms), brukerkontoer og offline-støtte.

### Kom i gang lokalt

1. **Installer avhengigheter**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-ui.txt
   ```

2. **Backend (API for innlogging og brukere)** – start først:
   ```bash
   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```
   Standard er lokal SQLite; sett `DATABASE_URL` og `OPS_JWT_SECRET` i `.env` for Postgres-testing.

3. **Desktop-appen** (nytt terminalvindu):
   ```bash
   source .venv/bin/activate
   python main_window.py
   ```
   Ved første kjøring: bruk **Registrer ny bedrift** på innloggingsskjermen, deretter velg dashboard på velkomstsiden.

Se **docs/BRUKERKONTOER_OG_OFFLINE.md** for mer om API, database og offline-arkitektur.

### Deploy backend til Vercel

- Repoet inneholder en `server.py` i roten som eksporterer FastAPI-appen (`backend.main.app`).  
- På Vercel:
  - Koble til GitHub-repoet ditt.
  - Root directory: rot på repoet (der `server.py` ligger).
  - Sett miljøvariabler: `OPS_JWT_SECRET` og `DATABASE_URL` (Postgres).
  - Vercel bruker `requirements.txt` og `server.py` automatisk for FastAPI-støtte, og eksponerer APIet på din Vercel-URL.

### Excel fra Microsoft Forms

- **Støttet format**: `.xlsx` (Forms eksporterer normalt til dette).
- **Auto-mapping**: I *Innstillinger → Kolonner* kan du trykke *Auto-map* for å mappe kolonner basert på header-tekst (case/whitespace/æøå-varianter håndteres).

### Bygg sentralen (drag & drop)

- Venstremenyen har en liste med bokser (Påtropp, Avtropp, Forsinket, Status, Logg).
- **Dra en boks** til et felt på hovedskjermen (“Slipp boks her”) for å plassere den.
- Standardoppsett fyller et **2x2-grid** med Påtropp og Avtropp ved siden av hverandre.

### Sikkerhet/robusthet (kort)

- **Kun** `.xlsx` og `.csv` aksepteres.
- **Størrelsesgrenser** for lokale filer og nedlasting fra URL.
- URL-nedlasting skjer til **midlertidig fil** som slettes etter innlesing.

### Tester

```bash
pip install -r requirements-dev.txt
pytest -q
```

