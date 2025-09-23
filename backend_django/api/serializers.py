from rest_framework import serializers
from .models import Document, DocumentChunk, ChatSession, ChatMessage

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "title", "source", "mime_type", "created_at", "file"]
        read_only_fields = ["id", "created_at"]


class DocumentUploadSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    file = serializers.FileField()


class DocumentChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChunk
        fields = ["id", "document", "chunk_index", "content", "vector_dim"]


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "created_at"]
        read_only_fields = ["id", "created_at"]


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ["id", "title", "created_at", "messages"]
        read_only_fields = ["id", "created_at", "messages"]


class ChatRequestSerializer(serializers.Serializer):
    # PUBLIC_INTERFACE
    def validate(self, attrs):
        """Validate payload for chat requests."""
        return super().validate(attrs)

    session_id = serializers.IntegerField(required=False)
    query = serializers.CharField()
    top_k = serializers.IntegerField(required=False, min_value=1, max_value=20)


class ChatResponseSerializer(serializers.Serializer):
    answer = serializers.CharField()
    session_id = serializers.IntegerField()
    sources = serializers.ListField(child=serializers.DictField())
