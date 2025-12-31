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


class Lead(models.Model):
    class LeadType(models.TextChoices):
        MARCHE_PUBLIC = "marche_public", "Marché Public"
        ENTREPRISE = "entreprise", "Entreprise"
        OFFRE_EMPLOI = "offre_emploi", "Offre d'Emploi"
    
    class ProjectType(models.TextChoices):
        GTB = "GTB", "GTB (Gestion Technique du Bâtiment)"
        GTEB = "GTEB", "GTEB (Génie Technique Électrique du Bâtiment)"
        CVC = "CVC", "CVC (Chauffage Ventilation Climatisation)"
        SUPERVISION = "supervision", "Supervision Bâtiment"
        ELECTRICITE = "electricite", "Électricité Bâtiment"
        AUTOMATISME = "automatisme", "Automatisme"
        MIXTE = "mixte", "Mixte"
    
    class Sector(models.TextChoices):
        HOPITAL = "hopital", "Hôpital"
        INDUSTRIE = "industrie", "Industrie"
        TERTIAIRE = "tertiaire", "Tertiaire"
        PUBLIC = "public", "Public"
        RESIDENTIEL = "residentiel", "Résidentiel"
        AUTRE = "autre", "Autre"
    
    class CompanySize(models.TextChoices):
        PETITE = "petite", "Petite (< 50 employés)"
        MOYENNE = "moyenne", "Moyenne (50-250 employés)"
        GRANDE = "grande", "Grande (> 250 employés)"
        INCONNU = "inconnu", "Inconnu"
    
    class Temperature(models.TextChoices):
        FROID = "froid", "Froid (0-39)"
        TIEDE = "tiede", "Tiède (40-69)"
        CHAUD = "chaud", "Chaud (70-100)"
    
    # Informations de base
    lead_type = models.CharField(max_length=20, choices=LeadType.choices)
    project_type = models.CharField(max_length=20, choices=ProjectType.choices, null=True, blank=True)
    
    # Informations du marché public ou entreprise
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    organization_name = models.CharField(max_length=255)  # Maître d'ouvrage ou nom entreprise
    website = models.URLField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True, null=True)
    
    # Localisation
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default="Maroc")
    
    # Informations marché public
    market_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    market_url = models.URLField(blank=True, null=True)
    
    # Enrichissement
    sector = models.CharField(max_length=20, choices=Sector.choices, null=True, blank=True)
    company_size = models.CharField(max_length=20, choices=CompanySize.choices, default=CompanySize.INCONNU)
    
    # Scoring IA
    score = models.IntegerField(default=0)  # Score de 0 à 100
    temperature = models.CharField(max_length=10, choices=Temperature.choices, default=Temperature.FROID)
    score_justification = models.TextField(blank=True)  # Justification du score
    
    # Métadonnées
    source_url = models.URLField(blank=True, null=True)
    keywords_found = models.JSONField(default=list, blank=True)  # Mots-clés détectés
    raw_data = models.JSONField(default=dict, blank=True)  # Données brutes de la source
    
    # Statut
    is_contacted = models.BooleanField(default=False)
    is_converted = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_analyzed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-score', '-created_at']
        indexes = [
            models.Index(fields=['-score', '-created_at']),
            models.Index(fields=['temperature']),
            models.Index(fields=['country', 'city']),
            models.Index(fields=['project_type']),
        ]
    
    def __str__(self):
        return f"{self.organization_name} - {self.title[:50]}"
