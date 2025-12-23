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

class TicketAnalysis(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", "Faible"
        MEDIUM = "medium", "Moyenne"
        HIGH = "high", "Élevée"
        URGENT = "urgent", "Urgente"
    
    class PublishMode(models.TextChoices):
        SUGGESTION = "suggestion", "Suggestion"
        AUTO = "auto", "Automatique"
    
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name='analysis')
    intention = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    priority = models.CharField(max_length=20, choices=Priority.choices)
    ai_response = models.TextField()
    publish_mode = models.CharField(max_length=20, choices=PublishMode.choices, default=PublishMode.SUGGESTION)
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
       
