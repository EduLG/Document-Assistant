from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document

_LOADER_BY_EXTENSION = {
    ".pdf": PyPDFLoader,
    ".txt": TextLoader,
    ".md": TextLoader,
}

SUPPORTED_EXTENSIONS = frozenset(_LOADER_BY_EXTENSION)


def load_document(file_path: str) -> list[Document]:
    extension = Path(file_path).suffix.lower()
    loader_cls = _LOADER_BY_EXTENSION.get(extension)
    if loader_cls is None:
        raise ValueError(f"Unsupported file extension: {extension}")
    return loader_cls(file_path).load()
