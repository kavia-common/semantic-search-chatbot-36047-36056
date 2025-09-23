from django.db import models

class Document(models.Model):
    """
    Stores uploaded documents with their metadata.
    """
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    source = models.CharField(max_length=100, blank=True, default='upload')
    mime_type = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.title} ({self.id})"


class DocumentChunk(models.Model):
    """
    Text chunks derived from a Document and indexed into FAISS.
    """
    id = models.BigAutoField(primary_key=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.PositiveIntegerField(default=0)
    content = models.TextField()
    # Storing vector dimension for reference/debugging
    vector_dim = models.PositiveIntegerField(default=384)

    class Meta:
        indexes = [
            models.Index(fields=["document", "chunk_index"]),
        ]


class ChatSession(models.Model):
    """
    A chat session to group messages.
    """
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255, default="New Chat")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"ChatSession {self.id} - {self.title}"


class ChatMessage(models.Model):
    """
    Stores chat messages exchanged between user and assistant.
    """
    ROLE_CHOICES = (
        ("user", "User"),
        ("assistant", "Assistant"),
        ("system", "System"),
    )
    id = models.BigAutoField(primary_key=True)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
