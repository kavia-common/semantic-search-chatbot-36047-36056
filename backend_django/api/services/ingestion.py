from typing import Tuple
import os

# PUBLIC_INTERFACE
def read_file_to_text(file_path: str, mime_type: str | None = None) -> Tuple[str, str]:
    """Read a file into text. For now, support plain text/markdown; others treated as text bytes decode."""
    mt = (mime_type or "").lower()
    _, ext = os.path.splitext(file_path)
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        text = data.decode("utf-8", errors="ignore")
        return text, mt or ext.lower().strip(".")
    except Exception as e:
        raise RuntimeError(f"Failed to read file {file_path}: {e}")
