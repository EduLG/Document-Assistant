# Document Assistant

RAG document assistant: upload a PDF, chat about its content. FastAPI + LangChain (Gemini) backend, React + Vite frontend.

## Run with Docker

```bash
cp backend/.env.example backend/.env   # fill in GOOGLE_API_KEY
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000 (docs at `/docs`)

Indexed documents and vectors persist in the `chroma_data` / `upload_data` Docker volumes across restarts. Run `docker compose down -v` to wipe them.

## Run locally without Docker

See `backend/README.md` and `frontend/README.md`.
