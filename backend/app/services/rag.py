from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings

embeddings = GoogleGenerativeAIEmbeddings(
    model=settings.embedding_model,
    google_api_key=settings.google_api_key,
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

splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)

# conversation_id -> [(role, text), ...]
conversations: dict[str, list[tuple[str, str]]] = {}

SYSTEM_PROMPT = (
    "Eres un asistente que responde preguntas basándose únicamente en el contexto "
    "de los documentos proporcionados. Si la respuesta no está en el contexto, dilo "
    "claramente en lugar de inventar información. Responde en el mismo idioma que la pregunta."
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


def ingest_pdf(file_path: str, source_name: str) -> int:
    loader = PyPDFLoader(file_path)
    pages = loader.load()
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
        f"Contexto de los documentos:\n{context if context else '(sin contexto relevante encontrado)'}\n\n"
        f"Historial de la conversación:\n{history_text if history_text else '(sin historial previo)'}\n\n"
        f"Pregunta: {question}\n"
        "Respuesta:"
    )

    response = llm.invoke(prompt)
    answer = _extract_text(response.content)

    history.append(("Usuario", question))
    history.append(("IA", answer))

    return answer
