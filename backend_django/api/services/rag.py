from typing import Dict, List
from django.conf import settings
from ..models import Document, DocumentChunk
from .faiss_index import FaissIndex

# PUBLIC_INTERFACE
def retrieve(query: str, top_k: int | None = None) -> List[Dict]:
    """Retrieve top-k relevant chunks using FAISS and return sources metadata."""
    top_k = top_k or int(getattr(settings, "TOP_K", 5))
    index = FaissIndex()
    results = index.search(query, top_k=top_k)

    sources: List[Dict] = []
    for score, (doc_id, chunk_idx) in results:
        try:
            doc = Document.objects.get(id=doc_id)
            chunk = DocumentChunk.objects.filter(document_id=doc_id, chunk_index=chunk_idx).first()
        except Document.DoesNotExist:
            continue
        sources.append({
            "document_id": doc.id,
            "title": doc.title,
            "chunk_index": chunk_idx,
            "score": score,
            "snippet": (chunk.content[:400] + "...") if chunk and len(chunk.content) > 400 else (chunk.content if chunk else ""),
        })
    return sources


# PUBLIC_INTERFACE
def synthesize_answer(query: str, sources: List[Dict]) -> str:
    """Simple heuristic 'generation' composing answer from top snippets (placeholder for LLM)."""
    if not sources:
        return "I couldn't find relevant information in the knowledge base."
    header = f"Q: {query}\n\nBased on the documents, here is a summarized answer:\n"
    body = ""
    for idx, s in enumerate(sources[:3], start=1):
        body += f"\n[{idx}] {s.get('snippet','')}"
    footer = "\n\nNote: This answer is synthesized from retrieved document chunks."
    return header + body + footer
