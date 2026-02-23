# GitSync Agent 🤖

> Agentic Git Repository Lifecycle Manager — Python edition.

Manages the full lifecycle of a local Git repository: validation → sync verification → AI diff analysis → README update → safe cleanup. Each stage is handled by an independent agent with structured outputs and a full audit trail.

---

## Agent Architecture

```
sync_agent/
├── core/
│   ├── input_agent.py     → Validates path + remote. Returns ValidationResult.
│   ├── sync_agent.py      → Fetches remote, computes divergence. Returns SyncStatus + decision.
│   ├── update_agent.py    → Appends sync note, commits, pushes, verifies remote SHA.
│   └── cleanup_agent.py   → Archives (optional) + deletes local folder after confirmation.
├── ai/
│   └── analysis_agent.py  → Summarizes git diffs via Gemini (gemini-2.0-flash).
└── utils/
    ├── audit_agent.py     → Central audit agent: AuditEntry schema, NDJSON log, human console output.
    └── git_utils.py       → GitPython wrappers (fetch, diff, commit count).
```

**API server**: `server.py` — FastAPI, exposes all agents as REST endpoints, serves the React SPA from `dist/`.

---

## Quick Start

```bash
# 1. Clone / navigate to the project
cd gitsync_agent

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your Gemini API key
cp .env.example .env
# Edit .env → set GEMINI_API_KEY=your_key_here

# 5. Build the React frontend
yarn install
yarn build

# 6. Start the server
python server.py
# → Open http://localhost:3000
```

---

## REST API

| Method | Endpoint | Agent | Description |
|--------|----------|-------|-------------|
| `GET` | `/api/logs` | AuditAgent | Full audit trail |
| `GET` | `/api/ls?dir=` | — | Server-side directory browser |
| `POST` | `/api/init` | InputAgent | Validate path + remote |
| `POST` | `/api/verify` | SyncAgent | Fetch + compute divergence |
| `POST` | `/api/update-readme` | UpdateAgent | Commit sync note + push |
| `POST` | `/api/delete` | CleanupAgent | Archive + delete local folder |

---

## Running Tests

```bash
python -m pytest tests/ -v
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ | Google Gemini API key — loaded from `.env` |
| `PORT` | ❌ | Server port (default: `3000`) |

---

## Project Structure

```
gitsync_agent/
├── server.py              # FastAPI server
├── requirements.txt       # pip dependencies
├── pyproject.toml         # project metadata + pytest config
├── .env.example           # environment variable template
├── sync_agent/            # all agent modules (Python package)
├── tests/                 # pytest test suite
├── dist/                  # built React frontend (after yarn build)
└── to_be_deleted/         # old TypeScript sources (pending removal)
```
