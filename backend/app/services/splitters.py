from langchain_text_splitters import MarkdownTextSplitter, RecursiveCharacterTextSplitter, TextSplitter

from app.config import settings

_SPLITTER_CLS_BY_EXTENSION = {
    ".md": MarkdownTextSplitter,
}
_DEFAULT_SPLITTER_CLS = RecursiveCharacterTextSplitter


def get_splitter(extension: str) -> TextSplitter:
    splitter_cls = _SPLITTER_CLS_BY_EXTENSION.get(extension, _DEFAULT_SPLITTER_CLS)
    return splitter_cls(chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)
