from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

from .models import Document, DocumentChunk, ChatSession, ChatMessage
from .serializers import (
    DocumentSerializer,
    DocumentUploadSerializer,
    ChatRequestSerializer,
    ChatResponseSerializer,
    ChatSessionSerializer,
)
from .services.chunker import chunk_text
from .services.faiss_index import FaissIndex
from .services.ingestion import read_file_to_text
from .services.rag import retrieve, synthesize_answer


@swagger_auto_schema(method='get',
                     operation_id="health_check",
                     operation_summary="Health check",
                     operation_description="Returns server health status.",
                     tags=["System"],
                     responses={200: openapi.Response("OK")})
@api_view(['GET'])
def health(request):
    """Health check endpoint."""
    return Response({"message": "Server is up!"}, status=200)


# PUBLIC_INTERFACE
@swagger_auto_schema(method='post',
                     operation_id="upload_document",
                     operation_summary="Upload a document",
                     operation_description="Upload a document to the knowledge base. The document is chunked and indexed into FAISS.",
                     tags=["Documents"],
                     request_body=DocumentUploadSerializer,
                     responses={201: DocumentSerializer})
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_document(request):
    """
    Accepts multipart/form-data with fields:
    - title: string
    - file: file
    Returns created document metadata.
    """
    serializer = DocumentUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    title = serializer.validated_data.get("title") or ""
    file_obj = serializer.validated_data["file"]
    # Default title to filename if not provided
    try:
        inferred_title = getattr(file_obj, "name", "") or "Untitled"
        # Remove extension for nicer titles
        if "." in inferred_title:
            inferred_title = inferred_title.rsplit(".", 1)[0] or inferred_title
    except Exception:
        inferred_title = "Untitled"
    if not title:
        title = inferred_title

    with transaction.atomic():
        doc = Document.objects.create(
            title=title, file=file_obj, source="upload", mime_type=getattr(file_obj, "content_type", "") or ""
        )
        doc.save()

        # Read and chunk content
        text, _ = read_file_to_text(doc.file.path, doc.mime_type)
        chunks = chunk_text(text)

        # Persist chunks and index to FAISS
        dim = int(getattr(settings, "EMBEDDING_DIM", 384))
        for idx, c in enumerate(chunks):
            DocumentChunk.objects.create(document=doc, chunk_index=idx, content=c, vector_dim=dim)

        # Build vectors
        index = FaissIndex(dim=dim)
        index.add_text_chunks(document_id=doc.id, chunks=chunks, vector_dim=dim)

    return Response(DocumentSerializer(doc).data, status=status.HTTP_201_CREATED)


# PUBLIC_INTERFACE
@swagger_auto_schema(method='get',
                     operation_id="list_documents",
                     operation_summary="List documents",
                     operation_description="List all uploaded documents with metadata.",
                     tags=["Documents"],
                     responses={200: openapi.Response("List of documents")})
@api_view(['GET'])
def list_documents(request):
    """List all documents."""
    docs = Document.objects.order_by("-created_at")
    return Response(DocumentSerializer(docs, many=True).data, status=200)


# PUBLIC_INTERFACE
@swagger_auto_schema(method='get',
                     operation_id="get_document",
                     operation_summary="Get document by ID",
                     operation_description="Retrieve a document metadata and chunk counts.",
                     tags=["Documents"],
                     manual_parameters=[openapi.Parameter('doc_id', openapi.IN_PATH, description="Document ID", type=openapi.TYPE_INTEGER)],
                     responses={200: openapi.Response("Document details")})
@api_view(['GET'])
def get_document(request, doc_id: int):
    """Get one document by ID."""
    doc = get_object_or_404(Document, pk=doc_id)
    data = DocumentSerializer(doc).data
    data["chunks"] = doc.chunks.count()
    return Response(data, status=200)


# PUBLIC_INTERFACE
@swagger_auto_schema(method='post',
                     operation_id="chat",
                     operation_summary="Chat with RAG",
                     operation_description="Send a message to the chatbot. Retrieves relevant chunks via FAISS and synthesizes an answer. Creates or appends to a chat session and saves messages.",
                     tags=["Chat"],
                     request_body=ChatRequestSerializer,
                     responses={200: ChatResponseSerializer})
@api_view(['POST'])
@parser_classes([JSONParser])
def chat(request):
    """
    Chat endpoint.
    - Body: { "query": "your question", "session_id": optional int, "top_k": optional int }
    - Returns: { "answer": str, "session_id": int, "sources": [ ... ] }
    """
    serializer = ChatRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    query = serializer.validated_data["query"]
    top_k = serializer.validated_data.get("top_k")
    session_id = serializer.validated_data.get("session_id")

    # Retrieve context
    sources = retrieve(query, top_k=top_k)
    answer = synthesize_answer(query, sources)

    # Create/find session, store messages
    if session_id:
        session = get_object_or_404(ChatSession, pk=session_id)
    else:
        session = ChatSession.objects.create(title=query[:60] or "New Chat")

    ChatMessage.objects.create(session=session, role="user", content=query)
    ChatMessage.objects.create(session=session, role="assistant", content=answer)

    response = {
        "answer": answer,
        "session_id": session.id,
        "sources": sources,
    }
    return Response(response, status=200)


# PUBLIC_INTERFACE
@swagger_auto_schema(method='get',
                     operation_id="list_sessions",
                     operation_summary="List chat sessions",
                     operation_description="List all chat sessions with recent messages.",
                     tags=["Chat"],
                     responses={200: ChatSessionSerializer(many=True)})
@api_view(['GET'])
def list_sessions(request):
    """List chat sessions."""
    sessions = ChatSession.objects.order_by("-created_at")
    return Response(ChatSessionSerializer(sessions, many=True).data, status=200)


# PUBLIC_INTERFACE
@swagger_auto_schema(method='get',
                     operation_id="get_session",
                     operation_summary="Get a chat session by ID",
                     operation_description="Retrieve a chat session and its messages.",
                     tags=["Chat"],
                     manual_parameters=[openapi.Parameter('session_id', openapi.IN_PATH, description="Session ID", type=openapi.TYPE_INTEGER)],
                     responses={200: ChatSessionSerializer})
@api_view(['GET'])
def get_session(request, session_id: int):
    """Get single chat session by ID."""
    session = get_object_or_404(ChatSession, pk=session_id)
    return Response(ChatSessionSerializer(session).data, status=200)
