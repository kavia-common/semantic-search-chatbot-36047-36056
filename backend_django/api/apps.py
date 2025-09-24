from django.apps import AppConfig
import os


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        """
        Optionally auto-seed test documents on startup if AUTO_SEED_STATIC_DOCS=true in environment.
        This is safe to call multiple times; seeding skips docs that already exist.
        """
        try:
            auto_seed = os.getenv("AUTO_SEED_STATIC_DOCS", "false").lower() == "true"
            if not auto_seed:
                return

            # Deferred import to avoid app registry issues
            from .services.seeder import seed_static_documents

            docs = [
                {
                    "title": "RAG Overview",
                    "mime_type": "text/plain",
                    "source": "static-seed",
                    "content": (
                        "Retrieval-Augmented Generation (RAG) combines retrieval with generation. "
                        "A retriever fetches semantically relevant chunks; a generator composes an answer."
                    ),
                },
                {
                    "title": "FAISS Basics",
                    "mime_type": "text/plain",
                    "source": "static-seed",
                    "content": (
                        "FAISS provides efficient nearest neighbor search over dense vectors. "
                        "With normalized embeddings, inner product approximates cosine similarity."
                    ),
                },
                {
                    "title": "Chunking Strategy",
                    "mime_type": "text/plain",
                    "source": "static-seed",
                    "content": (
                        "Fixed-size windows with overlap preserve context across chunk boundaries. "
                        "Example: size=800, overlap=80."
                    ),
                },
            ]
            seed_static_documents(docs)
        except Exception:
            # Avoid breaking startup if seeding fails
            pass
