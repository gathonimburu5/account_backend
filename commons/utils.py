import os
from rest_framework import serializers

def validate_file_size(file):
    allowed = [".jpg", ".jpeg", ".png", ".pdf", ".webp"]
    extension = os.path.splitext(file.name)[1].lower()
    if extension not in allowed:
        raise serializers.ValidationError(f"Unsupported file extension. Allowed extensions are: {', '.join(allowed)}")
    if file.size > 2 * 1024 * 1024:  # 2MB limit
        raise serializers.ValidationError("File size exceeds the maximum limit of 2MB.")
    return file

def validate_upload_file(file):
    allowed = [".pdf", ".docx", ".xlsx", ".pptx"]
    extension = os.path.splitext(file.name)[1].lower()
    if extension not in allowed:
        raise serializers.ValidationError(f"Unsupported file extension. Allowed extensions are: {', '.join(allowed)}")
    return file

