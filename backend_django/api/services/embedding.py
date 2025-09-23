import threading
from typing import List

from django.conf import settings

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover
    SentenceTransformer = None

_model_lock = threading.Lock()
_model_instance = None

# PUBLIC_INTERFACE
def get_embedding_model():
    """Return a shared instance of the embedding model based on EMBEDDING_MODEL_NAME."""
    global _model_instance
    if _model_instance is not None:
        return _model_instance
    with _model_lock:
        if _model_instance is None:
            if SentenceTransformer is None:
                raise RuntimeError("sentence-transformers not installed. Add it to requirements.txt")
            _model_instance = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
    return _model_instance


# PUBLIC_INTERFACE
def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a list of texts to dense vectors."""
    model = get_embedding_model()
    vectors = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return vectors.tolist()
