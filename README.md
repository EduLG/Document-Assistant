# Document Assistant

A Retrieval-Augmented Generation (RAG) assistant: upload documents, then ask questions about their content. FastAPI + LangChain (Gemini) backend, React + Vite frontend.

This project is being built incrementally, phase by phase, as a hands-on exploration of how a RAG system evolves from "it technically works" into something closer to production-grade. This README explains both **what exists today** and **why the rest of the roadmap looks the way it does** — the reasoning matters as much as the checklist.

## Current status

| Phase | Goal | Status |
|---|---|---|
| 0 — MVP frontend | Minimal upload + chat UI | ✅ Done |
| 1 — Functional basic RAG | Multi-format ingestion, better splitting, caching, real retrieval chain, hybrid search | 🔄 In progress (2/6) |
| 2 — Retrieval improvement | Contextual compression, multi-query retrieval | ⬜ Not started |
| 3 — Agent conversion (LangGraph) | Turn the linear chain into a decision-making agent | ⬜ Not started |
| 4 — Production hardening | Multi-user isolation, observability, tests, PII safety | ⬜ Not started |
| 5 — Frontend advanced features | Document management, richer UI states | ⬜ Not started |

Full backlog lives in Jira (project **DA**).

## How it works today

### Upload pipeline — `POST /documents/upload`

```
client sends one or more files (.pdf / .txt / .md)
        │
        ▼
1. Every file's extension is validated against SUPPORTED_EXTENSIONS
   before anything is written to disk (fail-fast: a bad file anywhere
   in the batch aborts the whole request, no partial writes)
        │
        ▼
2. Each file is saved under UPLOAD_DIR with a UUID-prefixed name
        │
        ▼
3. loaders.load_document(path)
   → picks PyPDFLoader (.pdf) or TextLoader (.txt, .md) by extension
   → returns list[Document]  (LangChain's common unit: page_content + metadata)
        │
        ▼
4. splitters.get_splitter(extension)
   → MarkdownTextSplitter for .md (splits along # headings, code fences,
     horizontal rules — falls back to generic separators after that)
   → RecursiveCharacterTextSplitter for everything else (paragraph → line
     → word → character, in that priority order)
   → chunk_size / chunk_overlap are read from config (env vars), not hardcoded
        │
        ▼
5. Each resulting chunk is tagged with metadata["source"] = original filename
        │
        ▼
6. vectorstore.add_documents(chunks)
   → GoogleGenerativeAIEmbeddings turns each chunk into a vector
   → Chroma persists both the vectors and the original text under CHROMA_DIR
        │
        ▼
7. Response: [{filename, chunks_indexed}, ...] — one entry per uploaded file
```

The loader and splitter steps are both **dispatch tables** (`extension → class`), not hardcoded branches — the same shape of code, reused twice, because "pick the right strategy for this file type" is the same problem in both places. Adding support for a new file type later means adding one dictionary entry, not rewriting logic.

### Chat pipeline — `POST /chat`

```
{conversation_id, message}
        │
        ▼
1. vectorstore.similarity_search(message, k=4)
   → embeds the question, returns the 4 nearest chunks across
     every document ever indexed (there is no per-document or
     per-user scoping yet — see "known limitations" below)
        │
        ▼
2. Build one prompt: SYSTEM_PROMPT + retrieved context
   + last 6 turns of this conversation's history + the question
   (history lives in an in-process dict: conversation_id -> [(role, text), ...])
        │
        ▼
3. llm.invoke(prompt)  → Gemini chat model generates the answer
        │
        ▼
4. History is updated in place, the answer is returned
```

### Known limitations of today's implementation

These are not bugs — they're the parts of the roadmap that haven't been built yet, called out explicitly so it's clear what "done" currently means:

- **One shared vector collection.** Every document lands in a single Chroma collection named `documents`. There's no way to scope a search to one document, let alone one user.
- **Conversation history is a plain Python dict in memory.** Restart the backend, every conversation is gone.
- **No embedding cache.** Re-uploading the same content recomputes embeddings from scratch — each call is a billed request to Gemini.
- **Retrieval is pure vector similarity.** Great at semantic/paraphrase matching, weak at exact keywords, acronyms, or rare terms that don't have a nearby vector neighbor.
- **No user boundary at all.** Any conversation can retrieve any uploaded document.

## Where this is headed, and why

### Phase 1 — Functional basic RAG (current)

- **Embeddings with disk cache** — embedding a chunk is a network call. Without a cache, identical content (re-uploads, overlapping chunks across documents) costs money and time repeatedly for the same result.
- **Persistent Chroma vector store with per-document collection** — moves off the single shared collection, so retrieval can be scoped to a specific document instead of searching everything ever uploaded. This is also the foundation the multi-user isolation in Phase 4 builds on.
- **Q&A chain with conversational memory** — replaces the hand-rolled history dict + string concatenation with a real LangChain conversational chain, which also handles *query rewriting*: if you ask "what is X" and then "how does it compare to Y", the chain needs to resolve what "it" refers to.
- **Hybrid search (BM25 + vector)** — BM25 is classic keyword-ranking; combining it with vector similarity catches exact-term and acronym queries that pure semantic search tends to miss.

### Phase 2 — Retrieval improvement

- **Contextual compression retriever** — a retrieved chunk (e.g. 1000 characters) is often mostly irrelevant filler around one useful sentence. This post-processes each chunk to keep only what's actually relevant to the question *before* it reaches the LLM prompt — smaller prompts, less noise to distract the model.
- **Multi-query retriever for ambiguous questions** — one phrasing of a question can miss chunks that are relevant but worded very differently. The LLM generates several rephrasings, retrieval runs for each, and the results are merged — improving recall on vaguely-worded questions.

### Phase 3 — Conversion to agent (LangGraph)

- **StateGraph: classify → decide retrieval → retrieve → answer → self-validate** — today `/chat` always retrieves and always answers, unconditionally. A real agent should first classify the question (is this even answerable from the documents, or a greeting?), *decide* whether retrieval is needed, retrieve if so, answer, and finally check its own answer against the retrieved evidence before returning it — catching hallucinations before the user sees them. LangGraph models this as an explicit decision graph instead of a fixed linear chain.
- **SQLite checkpointing to persist conversations** — replaces the in-memory dict with real persistence, so conversations survive a server restart.
- **Human-in-the-loop when confidence is low** — a safety net: if self-validation flags low confidence (thin or contradictory context), the agent pauses and flags it instead of confidently guessing.

### Phase 4 — Production

- **Harden the FastAPI API** — rate limiting, upload size limits, a real error taxonomy.
- **Multi-user support with metadata-filtering isolation** — builds on the per-document collections from Phase 1: every chunk gets a user/tenant id in its metadata, and every retrieval call filters by it, so users never see each other's documents despite sharing the same underlying store. This is the standard, cost-effective multi-tenancy pattern for vector databases.
- **Structured logging and observability with LangSmith** — once there's a multi-step agent (classify/retrieve/answer/validate), print-debugging isn't enough. LangSmith traces every step of a run, showing exactly which retrieved chunks produced which answer.
- **Response caching and tests with pytest** — cache identical Q&A pairs to cut latency/cost; a test suite to prevent regressions as the pipeline grows more branches.
- **PII sanitization in documents and responses** — uploaded documents may contain personal data. Detecting and redacting it before indexing (and before returning answers) matters the moment this stops being a personal sandbox project.

### Phase 5 — Web frontend: advanced features

- **Document management (list/delete)** — today's UI can only add documents, never see or remove what's already indexed.
- **Loading, error, and feedback states** — hardens the UX beyond the current minimal toast-based feedback.

### The end state

Put together, the target system is a multi-user, agentic RAG assistant: an incoming question is classified, retrieval is decided rather than assumed, evidence is gathered through hybrid search scoped to the asking user's own documents and refined through multi-query expansion and contextual compression, the answer is self-validated against that evidence and escalated to a human when uncertain, conversation state is durably persisted, and the whole pipeline is observable, tested, rate-limited, and PII-safe. Today's implementation — always retrieve, always answer, one shared collection, in-memory history — is the deliberately simple first slice that each phase above builds on, one well-scoped capability at a time.

## Tech stack

- **Backend**: FastAPI, LangChain (`langchain-community`, `langchain-chroma`, `langchain-text-splitters`, `langchain-google-genai`), Google Gemini (chat + embeddings), ChromaDB, pypdf
- **Frontend**: React 19, Vite, TypeScript, Tailwind CSS v4, Radix UI
- **Infra**: Docker Compose (backend + frontend containers), named volumes for persistent vector store and uploads

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

## Configuration

All backend configuration is via environment variables (`backend/.env`, see `backend/.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `GOOGLE_API_KEY` | *(required)* | Gemini API key for chat + embeddings |
| `CHAT_MODEL` | `gemini-3.6-flash` | Chat model used to generate answers |
| `EMBEDDING_MODEL` | `models/gemini-embedding-001` | Embedding model used to index and search |
| `CHROMA_DIR` | `./chroma_db` | Where the vector store persists to disk |
| `UPLOAD_DIR` | `./data/uploads` | Where uploaded files are saved |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed origins for the frontend |
| `CHUNK_SIZE` | `1000` | Target chunk size (characters) when splitting documents |
| `CHUNK_OVERLAP` | `150` | Overlap (characters) between consecutive chunks |
