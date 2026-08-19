from django.db import models

class Company(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    registration_number = models.CharField(max_length=100)
    registration_date = models.DateField()
    kra_number = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    postal_address = models.CharField(max_length=100)
    physical_address = models.CharField(max_length=200)
    county = models.CharField(max_length=100,)
    logo = models.ImageField(upload_to="companies/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
