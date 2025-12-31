from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User
from .models import User, Ticket
from .models import TicketAnalysis, Lead


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active']

class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'password']
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = '__all__'


class TicketAnalysisSerializer(serializers.ModelSerializer):
    ticket = TicketSerializer(read_only=True)
    class Meta:
        model = TicketAnalysis
        fields = '__all__'


class LeadSerializer(serializers.ModelSerializer):
    """Serializer pour les leads GTB/GTEB"""
    class Meta:
        model = Lead
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'last_analyzed_at']
    
    def to_representation(self, instance):
        """Formatage personnalisé pour l'affichage"""
        data = super().to_representation(instance)
        
        # Formater les dates
        if data.get('market_date'):
            data['market_date'] = instance.market_date.strftime('%Y-%m-%d') if instance.market_date else None
        
        # Formater le budget
        if data.get('budget'):
            data['budget'] = float(instance.budget) if instance.budget else None
        
        return data


class LeadSearchRequestSerializer(serializers.Serializer):
    """Serializer pour les requêtes de recherche de leads"""
    countries = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=['Maroc', 'France', 'Canada']
    )
    max_leads_per_source = serializers.IntegerField(default=50, min_value=1, max_value=200)
