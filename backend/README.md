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
- `POST /documents/upload` — multipart/form-data, one or more files under the repeated field `files` (`.pdf`, `.txt`, `.md`); returns a `doc_id` per file
- `POST /chat` — JSON `{"conversation_id": "...", "message": "...", "doc_ids": ["..."]}` (`doc_ids` optional; omit it to search all documents)

## Notes

- Vector store: persistent Chroma in `chroma_db/` (gitignored), single shared collection; each chunk carries a `doc_id` in its metadata so retrieval can be scoped to one or more documents (DA-8, Phase 1).
- Documents are loaded and split per file type (`app/services/loaders.py`, `app/services/splitters.py`) — PDF/plain text use the generic recursive splitter, Markdown uses a heading-aware one. `CHUNK_SIZE` / `CHUNK_OVERLAP` in `.env` control both.
- Conversation history lives in the process's memory (lost on server restart); real persistence is DA-14 (Phase 3).
- Models configurable via `CHAT_MODEL` / `EMBEDDING_MODEL` in `.env` — Gemini model availability changes over time; if you get a 404, check which models your API key supports.
