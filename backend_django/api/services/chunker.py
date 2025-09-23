from typing import List
from django.conf import settings

# PUBLIC_INTERFACE
def chunk_text(text: str) -> List[str]:
    """Naive text chunker by character windows with overlap."""
    size = int(getattr(settings, "CHUNK_SIZE", 800))
    overlap = int(getattr(settings, "CHUNK_OVERLAP", 80))
    if size <= 0:
        return [text]
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + size, n)
        chunks.append(text[start:end])
        if end == n:
            break
        start = max(0, end - overlap)
    return chunks
