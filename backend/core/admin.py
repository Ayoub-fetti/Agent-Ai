from django.contrib import admin
from .models import Lead, Ticket, TicketAnalysis

# Register your models here.

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['organization_name', 'title', 'city', 'country', 'score', 'temperature', 'project_type', 'is_contacted', 'created_at']
    list_filter = ['temperature', 'country', 'project_type', 'sector', 'lead_type', 'is_contacted', 'is_converted']
    search_fields = ['organization_name', 'title', 'description', 'city', 'email']
    readonly_fields = ['created_at', 'updated_at', 'last_analyzed_at']
    fieldsets = (
        ('Informations de base', {
            'fields': ('lead_type', 'project_type', 'title', 'description', 'organization_name')
        }),
        ('Contact', {
            'fields': ('email', 'phone', 'website', 'city', 'country')
        }),
        ('Marché public', {
            'fields': ('market_date', 'budget', 'market_url'),
            'classes': ('collapse',)
        }),
        ('Enrichissement', {
            'fields': ('sector', 'company_size'),
            'classes': ('collapse',)
        }),
        ('Scoring', {
            'fields': ('score', 'temperature', 'score_justification', 'keywords_found'),
        }),
        ('Statut', {
            'fields': ('is_contacted', 'is_converted', 'notes')
        }),
        ('Métadonnées', {
            'fields': ('source_url', 'raw_data', 'created_at', 'updated_at', 'last_analyzed_at'),
            'classes': ('collapse',)
        }),
    )
