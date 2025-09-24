from typing import Tuple, IO, Optional
import os

try:
    import chardet  # type: ignore
except Exception:  # pragma: no cover
    chardet = None

# Best-effort optional imports; we guard usage below.
try:
    from PyPDF2 import PdfReader  # type: ignore
except Exception:  # pragma: no cover
    PdfReader = None

try:
    import docx  # python-docx
except Exception:  # pragma: no cover
    docx = None


def _safe_decode_text_bytes(data: bytes) -> str:
    """
    Try to decode bytes into text:
    - If chardet is available, detect encoding first.
    - Fallback to UTF-8 with replacement.
    """
    if chardet:
        try:
            det = chardet.detect(data) or {}
            enc = det.get("encoding") or "utf-8"
            return data.decode(enc, errors="replace")
        except Exception:
            pass
    return data.decode("utf-8", errors="replace")


def _read_text_from_pdf_bytes(data: bytes) -> str:
    """Extract text from a PDF using PyPDF2 if available; else return empty string."""
    if not PdfReader:
        return ""
    try:
        # PdfReader accepts a file-like, so wrap bytes
        import io
        reader = PdfReader(io.BytesIO(data))
        parts = []
        for page in getattr(reader, "pages", []):
            try:
                txt = page.extract_text() or ""
            except Exception:
                txt = ""
            if txt:
                parts.append(txt)
        return "\n".join(parts).strip()
    except Exception:
        return ""


def _read_text_from_docx_bytes(data: bytes) -> str:
    """Extract text from a DOCX using python-docx if available; else return empty string."""
    if not docx:
        return ""
    try:
        import io
        document = docx.Document(io.BytesIO(data))
        return "\n".join(p.text for p in document.paragraphs if p.text).strip()
    except Exception:
        return ""


def _load_bytes(file_obj: Optional[IO[bytes]] = None, file_path: Optional[str] = None) -> bytes:
    """
    Load file content as bytes from either a file-like object or file path.
    Preference: file_obj if provided; otherwise file_path must be provided.
    """
    if file_obj is not None:
        try:
            # Ensure at beginning
            try:
                file_obj.seek(0)
            except Exception:
                pass
            return file_obj.read()
        except Exception as e:
            raise RuntimeError(f"Failed reading uploaded stream: {e}")
    if not file_path:
        raise RuntimeError("No file content source provided")
    try:
        with open(file_path, "rb") as f:
            return f.read()
    except Exception as e:
        raise RuntimeError(f"Failed to read file {file_path}: {e}")


# PUBLIC_INTERFACE
def read_file_to_text(file_path: Optional[str] = None,
                      mime_type: Optional[str] = None,
                      file_obj: Optional[IO[bytes]] = None) -> Tuple[str, str]:
    """
    Read a file into text safely.

    Args:
        file_path: Optional filesystem path to the file (for stored uploads).
        mime_type: Optional MIME type string, used to guide parsing.
        file_obj: Optional file-like object (e.g., InMemoryUploadedFile or TemporaryUploadedFile).

    Returns:
        (text, detected_type) where detected_type is a short label like 'txt', 'pdf', 'docx', or extension.

    Behavior:
        - Supports UTF-8/plain text and markdown by decoding bytes.
        - If PDF and PyPDF2 available, extracts text.
        - If DOCX and python-docx available, extracts text.
        - Falls back to best-effort text decoding with encoding detection when possible.

    Raises:
        RuntimeError on I/O issues.
    """
    mt = (mime_type or "").lower().strip()
    ext = ""
    if file_path:
        _, ext = os.path.splitext(file_path)
        ext = ext.lower().lstrip(".")

    data = _load_bytes(file_obj=file_obj, file_path=file_path)

    # Decide parsing strategy
    type_hint = mt or ext

    # PDF
    if ("pdf" in type_hint) or (ext == "pdf"):
        text = _read_text_from_pdf_bytes(data)
        if text:
            return text, "pdf"
        # if PDF parser failed, fall through to generic decode

    # DOCX
    if ("vnd.openxmlformats-officedocument.wordprocessingml.document" in type_hint) or (ext == "docx"):
        text = _read_text_from_docx_bytes(data)
        if text:
            return text, "docx"
        # fall through

    # Plain text-ish (txt, md, csv, json, etc) or unknown
    text = _safe_decode_text_bytes(data)
    detected = "txt" if (type_hint in {"", "text/plain", "txt", "md", "markdown"}) else (ext or type_hint or "txt")
    return text, detected
