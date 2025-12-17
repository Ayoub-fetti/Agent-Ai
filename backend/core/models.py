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