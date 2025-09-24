from django.conf import settings
from django.db import transaction

from ..models import Document, DocumentChunk
from .chunker import chunk_text
from .faiss_index import FaissIndex


# PUBLIC_INTERFACE
def seed_static_documents(docs: list[dict]) -> tuple[int, int]:
    """Seed static documents into DB and FAISS index.
    Returns: (created_documents_count, total_chunks_added)
    Each doc dict should have: title (str), content (str), optional mime_type (str), optional source (str)
    """
    dim = int(getattr(settings, "EMBEDDING_DIM", 384))
    index = FaissIndex(dim=dim)
    created_count = 0
    chunk_total = 0

    for d in docs:
        title = d.get("title") or "Untitled"
        source = d.get("source", "static-seed")
        if Document.objects.filter(title=title, source=source).exists():
            continue

        with transaction.atomic():
            doc = Document.objects.create(
                title=title,
                file="documents/static-seed.txt",
                source=source,
                mime_type=d.get("mime_type", "text/plain"),
            )
            chunks = chunk_text(d.get("content", ""))

            for idx, c in enumerate(chunks):
                DocumentChunk.objects.create(
                    document=doc,
                    chunk_index=idx,
                    content=c,
                    vector_dim=dim,
                )

            index.add_text_chunks(document_id=doc.id, chunks=chunks, vector_dim=dim)

            created_count += 1
            chunk_total += len(chunks)

    return created_count, chunk_total
