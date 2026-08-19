from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The email address is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email=email, password=password, **extra_fields)

class Permission(models.Model):
    code = models.CharField(max_length=150, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    module = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code

class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, related_name="roles", blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    roles = models.ManyToManyField(Role, related_name="users", blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True)
    is_email_verified = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    def has_permission(self, permission_codes):
        if not self.is_authenticated:
            return False
        if not self.is_active:
            return False
        if self.is_locked:
            return False
        if self.is_deleted:
            return False
        user_permissions = set(self.roles.filter(is_active=True, permissions__is_active=True,).values_list("permissions__code", flat=True,))
        return set(permission_codes).issubset(user_permissions)

    def __str__(self):
        return self.email