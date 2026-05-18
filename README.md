# ⚽ NextMove (TactiCore)

## Overview

This repository contains two versions of the NextMove project:

- **`web-app/`** — new FastAPI + HTML/JS web application with real-time sync.
- **`streamlit-legacy/`** — legacy Streamlit proof-of-concept and original analysis pages.

If you are looking for the current modern implementation, start in `web-app/`.

---

## Modern Web App

The current working app is located in `web-app/`.

- `web-app/backend/` — FastAPI backend, SQLite, WebSocket sync.
- `web-app/frontend/` — static SPA with HTML/CSS/JS.
- `web-app/README-WEB-APP.md` — detailed architecture and startup guide.
- `web-app/HOW-IT-WORKS.md` — explanation of how the code works.
- `web-app/QUICK-START.md` — quick setup instructions.
- `web-app/MIGRATION_GUIDE.md` — migration notes from Streamlit.

### Start the web app

```bash
cd web-app
chmod +x start-all.sh
./start-all.sh
```

---

## Legacy Streamlit App

The legacy application is preserved under `streamlit-legacy/`.

- `streamlit-legacy/app.py` — original Streamlit entry point.
- `streamlit-legacy/pages/` — streamlit pages.
- `streamlit-legacy/src/` — legacy business logic.
- `streamlit-legacy/READMEAPP.md` — legacy app documentation.
- `streamlit-legacy/requirements.txt` — dependencies for the legacy version.

Use the legacy folder only if you need the previous Streamlit prototype.

---

## Repository Layout

```
nextmove/
├── .env                        # local environment variables
├── .gitignore
├── README.md                   # this file
├── streamlit-legacy/           # legacy Streamlit proof-of-concept
└── web-app/                    # modern FastAPI + Web UI app
```

---

## Notes

- The modern app is intentionally isolated inside `web-app/`.
- The legacy app remains in `streamlit-legacy/` for reference.
- Do not expect the root folder to contain the current web app files.
