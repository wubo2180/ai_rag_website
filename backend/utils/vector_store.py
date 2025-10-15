from django.db import models

class VectorStore(models.Model):
    vector = models.JSONField()
    metadata = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"VectorStore(id={self.id}, created_at={self.created_at})"