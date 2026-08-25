from pathlib import Path

from langchain_chroma import Chroma
from langchain_classic.embeddings import CacheBackedEmbeddings
from langchain_classic.storage import LocalFileStore
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from app.config import settings
from app.services.loaders import load_document
from app.services.splitters import get_splitter

_underlying_embeddings = GoogleGenerativeAIEmbeddings(
    model=settings.embedding_model,
    google_api_key=settings.google_api_key,
)

embeddings = CacheBackedEmbeddings.from_bytes_store(
    underlying_embeddings=_underlying_embeddings,
    document_embedding_cache=LocalFileStore(settings.embeddings_cache_dir),
    namespace=settings.embedding_model,
    key_encoder="sha256",
)

vectorstore = Chroma(
    collection_name="documents",
    embedding_function=embeddings,
    persist_directory=settings.chroma_dir,
)

llm = ChatGoogleGenerativeAI(
    model=settings.chat_model,
    google_api_key=settings.google_api_key,
    temperature=0.2,
)

# conversation_id -> [(role, text), ...]
conversations: dict[str, list[tuple[str, str]]] = {}

SYSTEM_PROMPT = (
    "You are an assistant that answers questions based solely on the provided "
    "document context. If the answer is not in the context, say so clearly instead "
    "of making up information. Respond in the same language as the question."
)


def _extract_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        return "".join(parts)
    return str(content)


def ingest_document(file_path: str, source_name: str) -> int:
    pages = load_document(file_path)
    extension = Path(file_path).suffix.lower()
    splitter = get_splitter(extension)
    chunks = splitter.split_documents(pages)
    for chunk in chunks:
        chunk.metadata["source"] = source_name
    vectorstore.add_documents(chunks)
    return len(chunks)


def answer_question(conversation_id: str, question: str, k: int = 4) -> str:
    docs = vectorstore.similarity_search(question, k=k)
    context = "\n\n---\n\n".join(doc.page_content for doc in docs)

    history = conversations.setdefault(conversation_id, [])
    history_text = "\n".join(f"{role}: {text}" for role, text in history[-6:])

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Document context:\n{context if context else '(no relevant context found)'}\n\n"
        f"Conversation history:\n{history_text if history_text else '(no previous history)'}\n\n"
        f"Question: {question}\n"
        "Answer:"
    )

    response = llm.invoke(prompt)
    answer = _extract_text(response.content)

    history.append(("User", question))
    history.append(("AI", answer))

    return answer
