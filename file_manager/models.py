import os
import uuid

from django.db import models
from django.utils.text import get_valid_filename


def file_upload_path(instance: "File", filename: str) -> str:
    filename = get_valid_filename(os.path.basename(filename))
    if instance.folder:
        folder_path = instance.folder.path.lstrip("/")
    else:
        folder_path = ""
    return os.path.join("files", folder_path, filename) if folder_path else filename


class Folder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="subfolders")
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    root = models.BooleanField(default=False, editable=False)

    class Meta:
        unique_together = ("parent", "name")
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def path(self):
        parts, node = [], self
        while node:
            parts.append(node.name)
            node = node.parent
        return "/" + "/".join(reversed(parts))


class File(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to=file_upload_path)
    size = models.PositiveBigIntegerField(default=0, editable=False)
    mime_type = models.CharField(max_length=100, blank=True)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name="files", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("folder", "name")
        ordering = ["name"]

    def save(self, *args, **kwargs):
        self.size = self.file.size
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
