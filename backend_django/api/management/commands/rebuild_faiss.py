from django.core.management.base import BaseCommand
from api.models import Document, DocumentChunk
from api.services.faiss_index import FaissIndex

class Command(BaseCommand):
    help = "Rebuild the FAISS index from existing DocumentChunks."

    def handle(self, *args, **options):
        dim = 384
        index = FaissIndex(dim=dim)
        # Reinitialize empty index
        index._index.reset()
        index._ids = []

        total = 0
        for doc in Document.objects.all():
            chunks = list(
                DocumentChunk.objects.filter(document=doc)
                .order_by("chunk_index")
                .values_list("content", flat=True)
            )
            if not chunks:
                continue
            index.add_text_chunks(document_id=doc.id, chunks=chunks, vector_dim=dim)
            total += len(chunks)
        self.stdout.write(self.style.SUCCESS(f"Rebuilt FAISS index with {total} vectors."))
