from pathlib import Path

from langchain_chroma import Chroma
from langchain_classic.embeddings import CacheBackedEmbeddings
from langchain_classic.storage import LocalFileStore
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
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

# Per-session memory, lost on restart; persistent checkpointing is DA-14 (Phase 3).
session_histories: dict[str, InMemoryChatMessageHistory] = {}

# Only the most recent turns are sent to the model, to keep prompts bounded.
MAX_HISTORY_MESSAGES = 6

SYSTEM_PROMPT = (
    "You are an assistant that answers questions based solely on the provided "
    "document context. If the answer is not in the context, say so clearly instead "
    "of making up information. Respond in the same language as the question.\n\n"
    "Document context:\n{context}"
)

CONTEXTUALIZE_PROMPT = (
    "Given the conversation history and the latest user question, which may refer "
    "to earlier messages, rewrite it as a standalone question that can be understood "
    "without the history. Do not answer it; only return the rewritten question, "
    "in the same language as the original."
)

contextualize_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", CONTEXTUALIZE_PROMPT),
        MessagesPlaceholder("history"),
        ("human", "{question}"),
    ]
)

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("history"),
        ("human", "{question}"),
    ]
)

contextualize_chain = contextualize_prompt | llm | StrOutputParser()


def _get_session_history(conversation_id: str) -> BaseChatMessageHistory:
    return session_histories.setdefault(conversation_id, InMemoryChatMessageHistory())


def _doc_filter(doc_ids: list[str] | None) -> dict | None:
    if not doc_ids:
        return None
    return {"doc_id": doc_ids[0] if len(doc_ids) == 1 else {"$in": doc_ids}}


def _standalone_question(inputs: dict) -> str:
    # Follow-up questions ("how does it compare?") are rewritten so retrieval
    # gets a self-contained query; the first question needs no rewriting.
    if not inputs["history"]:
        return inputs["question"]
    return contextualize_chain.invoke(inputs)


def _retrieve(inputs: dict) -> list[Document]:
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": inputs["k"], "filter": _doc_filter(inputs.get("doc_ids"))}
    )
    return retriever.invoke(inputs["standalone_question"])


def _format_docs(docs: list[Document]) -> str:
    if not docs:
        return "(no relevant context found)"
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


rag_chain = (
    RunnablePassthrough.assign(history=lambda x: x["history"][-MAX_HISTORY_MESSAGES:])
    | RunnablePassthrough.assign(standalone_question=RunnableLambda(_standalone_question))
    | RunnablePassthrough.assign(context=RunnableLambda(_retrieve) | _format_docs)
    | qa_prompt
    | llm
    | StrOutputParser()
)

conversational_rag_chain = RunnableWithMessageHistory(
    rag_chain,
    _get_session_history,
    input_messages_key="question",
    history_messages_key="history",
)


def ingest_document(file_path: str, source_name: str, doc_id: str) -> int:
    pages = load_document(file_path)
    extension = Path(file_path).suffix.lower()
    splitter = get_splitter(extension)
    chunks = splitter.split_documents(pages)
    for chunk in chunks:
        chunk.metadata["source"] = source_name
        chunk.metadata["doc_id"] = doc_id
    vectorstore.add_documents(chunks)
    return len(chunks)


def answer_question(
    conversation_id: str, question: str, k: int = 4, doc_ids: list[str] | None = None
) -> str:
    return conversational_rag_chain.invoke(
        {"question": question, "k": k, "doc_ids": doc_ids},
        config={"configurable": {"session_id": conversation_id}},
    )
