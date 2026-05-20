# TraqCheck

Full-stack take-home: HR uploads a resume, the system extracts the candidate's profile, and an AI agent drafts a personalized request for PAN & Aadhaar.

## Stack

- **Backend** – Python 3.11+, FastAPI, SQLAlchemy (SQLite), LangChain (tool-calling agent)
- **Frontend** – React 18 + Vite + React Router
- **Resume parsing** – pypdf for PDFs, python-docx for DOCX
- **LLM** – OpenAI or Anthropic (auto-detected from env). Works without a key using a regex fallback so the UI is fully demoable.

## Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # add OPENAI_API_KEY or ANTHROPIC_API_KEY

uvicorn app.main:app --reload --port 8765
```

Health check: `GET http://127.0.0.1:8765/health`

OpenAPI docs are served at `http://127.0.0.1:8765/docs`.

### Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/candidates/upload` | Accept PDF/DOCX resume (multipart `file`). Returns the candidate; extraction runs in the background. |
| `GET` | `/candidates` | List all candidates (summary fields). |
| `GET` | `/candidates/{id}` | Full profile, extracted fields, confidence scores, document & request history. |
| `POST` | `/candidates/{id}/request-documents` | AI agent composes a personalized PAN/Aadhaar request and logs it. Optional body `{ "channel": "email" | "sms" }` overrides the agent's choice. |
| `POST` | `/candidates/{id}/submit-documents` | Multipart `pan` and/or `aadhaar` files. |

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite dev server runs on `http://localhost:5173` and proxies `/candidates` to the backend on port 8765.

## Notes

- Extraction happens in a FastAPI `BackgroundTask` after upload so the user gets immediate feedback. The dashboard and profile pages poll while a candidate is in `processing`.
- The AI agent uses LangChain's `create_tool_calling_agent`. It's given two tools (`draft_message`, `log_request`) and decides itself whether to use email or SMS based on what's on file.
- Confidence scores are produced by the LLM. The fallback path uses heuristic scores so the UI doesn't look empty without a key.
- Uploaded files land in `backend/uploads/`. SQLite DB sits at `backend/traqcheck.db`. Both paths are configurable via `.env`.
