import re
from rest_framework import serializers

def validate_password_stregth(password):
    if len(password) < 8:
        raise serializers.ValidationError("Password must contain at least 8 characters.")

    if not re.search(r"[A-Z]", password):
        raise serializers.ValidationError("Password must contain one uppercase letter.")

    if not re.search(r"[a-z]", password):
        raise serializers.ValidationError("Password must contain one lowercase letter.")

    if not re.search(r"\d", password):
        raise serializers.ValidationError("Password must contain one number.")

    return password