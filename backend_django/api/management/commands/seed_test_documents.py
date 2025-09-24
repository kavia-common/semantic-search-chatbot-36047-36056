from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction

from api.models import Document, DocumentChunk
from api.services.chunker import chunk_text
from api.services.faiss_index import FaissIndex


TEST_DOCS = [
    {
        "title": "RAG Overview",
        "mime_type": "text/plain",
        "source": "static-seed",
        "content": """Retrieval-Augmented Generation (RAG) is a technique that combines information retrieval
with text generation. In RAG, a retriever fetches relevant chunks from a knowledge base using semantic
search, and a generator composes an answer grounded in those chunks. This approach improves factuality,
reduces hallucinations, and allows the system to incorporate new knowledge without retraining the model.""",
    },
    {
        "title": "FAISS Basics",
        "mime_type": "text/plain",
        "source": "static-seed",
        "content": """FAISS (Facebook AI Similarity Search) is a library for efficient similarity search and clustering
of dense vectors. It supports a range of index types and can be used for nearest neighbor search in
embedding spaces. When embeddings are normalized, inner product corresponds to cosine similarity, enabling
fast and effective semantic search in applications like document retrieval.""",
    },
    {
        "title": "Chunking Strategy",
        "mime_type": "text/plain",
        "source": "static-seed",
        "content": """A simple chunking strategy uses fixed-size windows with overlap to maintain context between chunks.
For example, with size=800 characters and overlap=80, each subsequent chunk starts 80 characters before
the end of the previous one. This helps downstream retrieval models to capture context that spans boundaries.""",
    },
]


def _seed_documents():
    """
    Create a few static test documents, chunk them, store chunks, and index into FAISS.
    If a document with the same title and source already exists, it will be skipped.
    """
    dim = int(getattr(settings, "EMBEDDING_DIM", 384))
    index = FaissIndex(dim=dim)
    created_count = 0
    chunk_total = 0

    for d in TEST_DOCS:
        # Skip if already seeded (by title + source)
        exists = Document.objects.filter(title=d["title"], source=d.get("source", "static-seed")).exists()
        if exists:
            continue

        with transaction.atomic():
            # Create Document with a small placeholder file-like behavior.
            # The FileField requires a file, but for testing we can store a lightweight content-less file path
            # by using the title as a "logical" file. The ingestion for static seed uses the direct content below,
            # not the file path, so file presence is not required for the test flow.
            # We keep mime_type metadata for reference.
            doc = Document.objects.create(
                title=d["title"],
                file="documents/static-seed.txt",  # placeholder path (not used for reading)
                source=d.get("source", "static-seed"),
                mime_type=d.get("mime_type", "text/plain"),
            )

            # Chunk content
            content = d["content"]
            chunks = chunk_text(content)

            # Persist chunks
            for idx, c in enumerate(chunks):
                DocumentChunk.objects.create(
                    document=doc,
                    chunk_index=idx,
                    content=c,
                    vector_dim=dim,
                )

            # Index into FAISS
            index.add_text_chunks(document_id=doc.id, chunks=chunks, vector_dim=dim)

            created_count += 1
            chunk_total += len(chunks)

    return created_count, chunk_total


class Command(BaseCommand):
    help = "Seed a few static documents for testing (documents, chunks, FAISS index). Safe to run multiple times."

    def handle(self, *args, **options):
        created, chunks = _seed_documents()
        if created == 0:
            self.stdout.write(self.style.WARNING("No new documents seeded (already present)."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Seeded {created} documents with {chunks} chunks."))
