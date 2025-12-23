from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        AGENT_TECHNIQUE = "AGENT TECHNIQUE", "Agent Technique"
        AGENT_COMMERCIAL = "AGENT COMMERCIAL", "Agent Commercial"
    
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.AGENT_TECHNIQUE)
    is_active = models.BooleanField(default=True)

class Ticket(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Nouveau"
        OPEN = "open", "Ouvert"
        PENDING = "pending", "En attente"
        CLOSED = "closed", "Fermé"
    
    zammad_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices)
    customer_email = models.EmailField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    processed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
