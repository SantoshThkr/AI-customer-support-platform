import io
import re
from dataclasses import dataclass
from pathlib import PurePath

from fastapi import HTTPException, status
from pypdf import PdfReader
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models import (
    DocumentFileType,
    DocumentStatus,
    KnowledgeChunk,
    KnowledgeDocument,
    User,
)

FILE_TYPES = {
    ".txt": DocumentFileType.TXT,
    ".md": DocumentFileType.MARKDOWN,
    ".markdown": DocumentFileType.MARKDOWN,
    ".pdf": DocumentFileType.PDF,
}
CHUNK_SIZE = 1_000
HEADING_PATTERN = re.compile(r"^#{1,6}\s+(.+)$")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


@dataclass
class TextChunk:
    text: str
    section: str | None = None


@dataclass
class SearchResult:
    chunk: KnowledgeChunk
    score: float


def _bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def detect_file_type(filename: str) -> DocumentFileType:
    extension = PurePath(filename).suffix.lower()
    if extension not in FILE_TYPES:
        raise _bad_request("Unsupported file type. Upload a .txt, .md or .pdf file.")
    return FILE_TYPES[extension]


def extract_text(data: bytes, file_type: DocumentFileType) -> str:
    if file_type == DocumentFileType.PDF:
        if not data.startswith(b"%PDF-"):
            raise _bad_request("The file does not look like a PDF")
        try:
            reader = PdfReader(io.BytesIO(data))
            encrypted = reader.is_encrypted
            pages = [] if encrypted else [page.extract_text() or "" for page in reader.pages]
        except Exception as exc:  # pypdf raises many different errors for malformed files
            raise _bad_request("The PDF could not be read") from exc
        if encrypted:
            raise _bad_request("Encrypted PDFs are not supported")
        return "\n\n".join(pages)

    if b"\x00" in data:
        raise _bad_request("The file does not look like a text file")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise _bad_request("Text files must be UTF-8 encoded") from exc


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse runs of spaces/tabs but keep line breaks, which mark paragraphs.
    text = re.sub(r"[^\S\n]+", " ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_long_paragraph(paragraph: str, max_chars: int) -> list[str]:
    if len(paragraph) <= max_chars:
        return [paragraph]

    pieces: list[str] = []
    current = ""
    for sentence in SENTENCE_END.split(paragraph):
        while len(sentence) > max_chars:
            # A single enormous "sentence" (e.g. PDF text without punctuation).
            cut = sentence.rfind(" ", 0, max_chars)
            cut = cut if cut > 0 else max_chars
            pieces.append(sentence[:cut].strip())
            sentence = sentence[cut:].strip()
        if current and len(current) + len(sentence) + 1 > max_chars:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        pieces.append(current)
    return pieces


def split_into_chunks(text: str, max_chars: int = CHUNK_SIZE) -> list[TextChunk]:
    """Split cleaned text into paragraph-aligned chunks of at most max_chars.

    Markdown headings start a new chunk so each section is retrieved on its own,
    and the heading is kept as the chunk's section name.
    """
    chunks: list[TextChunk] = []
    parts: list[str] = []
    size = 0
    section: str | None = None
    chunk_section: str | None = None

    def flush() -> None:
        nonlocal parts, size
        if parts:
            chunks.append(TextChunk("\n\n".join(parts), chunk_section))
        parts, size = [], 0

    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        heading = HEADING_PATTERN.match(paragraph.split("\n", 1)[0])
        if heading:
            flush()
            section = heading.group(1).strip()

        for piece in _split_long_paragraph(paragraph, max_chars):
            if parts and size + len(piece) + 2 > max_chars:
                flush()
            if not parts:
                chunk_section = section
            parts.append(piece)
            size += len(piece) + 2

    flush()
    return chunks


def default_title(filename: str, text: str) -> str:
    """Use a Markdown document's first H1, otherwise a tidied-up file name."""
    first_line = text.split("\n", 1)[0]
    if first_line.startswith("# "):
        return first_line[2:].strip()
    stem = PurePath(filename).stem
    return re.sub(r"[-_]+", " ", stem).strip().capitalize() or "Untitled document"


def read_upload(file_obj, filename: str) -> tuple[DocumentFileType, str]:
    """Validate an uploaded file and return its type and cleaned text."""
    file_type = detect_file_type(filename)
    limit = settings.max_upload_size_mb * 1024 * 1024
    data = file_obj.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Files must be smaller than {settings.max_upload_size_mb} MB",
        )
    if not data:
        raise _bad_request("The file is empty")
    return file_type, clean_text(extract_text(data, file_type))


def create_document(
    db: Session,
    *,
    title: str,
    text: str,
    file_type: DocumentFileType,
    filename: str | None,
    uploaded_by: User | None,
) -> KnowledgeDocument:
    if not text:
        raise _bad_request("No text could be extracted from this document")

    document = KnowledgeDocument(
        title=title.strip()[:200],
        filename=filename,
        file_type=file_type,
        content=text,
        status=DocumentStatus.READY,
        uploaded_by_id=uploaded_by.id if uploaded_by else None,
    )
    for index, chunk in enumerate(split_into_chunks(text)):
        metadata = {"section": chunk.section} if chunk.section else {}
        document.chunks.append(
            KnowledgeChunk(chunk_index=index, chunk_text=chunk.text, metadata_=metadata)
        )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def keyword_search(db: Session, query: str, limit: int = 5) -> list[SearchResult]:
    # OR the words together: agents type questions, not exact phrases.
    words = re.findall(r"[a-z0-9]+", query.lower())
    if not words:
        return []
    ts_query = func.to_tsquery("english", " | ".join(words))
    rank = func.ts_rank_cd(KnowledgeChunk.search_vector, ts_query)
    rows = db.execute(
        select(KnowledgeChunk, rank)
        .options(joinedload(KnowledgeChunk.document))
        .where(KnowledgeChunk.search_vector.op("@@")(ts_query))
        .order_by(rank.desc(), KnowledgeChunk.id)
        .limit(limit)
    ).all()
    return [SearchResult(chunk=chunk, score=float(score)) for chunk, score in rows]
