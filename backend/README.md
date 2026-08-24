# Backend — Document Assistant (DA-21)

Minimal FastAPI: upload a PDF and chat about its content (RAG with Gemini).

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in GOOGLE_API_KEY
```

## Run

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

## Endpoints

- `GET /health`
- `POST /documents/upload` — multipart/form-data, field `file` (PDF)
- `POST /chat` — JSON `{"conversation_id": "...", "message": "..."}`

## Notes

- Vector store: persistent Chroma in `chroma_db/` (gitignored).
- Conversation history lives in the process's memory (lost on server restart); real persistence is DA-14 (Phase 3).
- Models configurable via `CHAT_MODEL` / `EMBEDDING_MODEL` in `.env` — Gemini model availability changes over time; if you get a 404, check which models your API key supports.
