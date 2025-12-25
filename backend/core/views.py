from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from .models import User
from .serializers import LoginSerializer, UserSerializer, CreateUserSerializer
from .permissions import IsAdmin
from .services.zammad_sync import ZammadSyncService
from .models import User, Ticket
from .serializers import LoginSerializer, UserSerializer, CreateUserSerializer, TicketSerializer
from .services.zammad_api import ZammadAPIService
from django.utils import timezone


@api_view(['GET'])
def health_check(request):
    return Response({'status': 'ok'})

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )
        if user and user.is_active:
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            })
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data['refresh']
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Logout successful'})
    except:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    return Response(UserSerializer(request.user).data)

@api_view(['POST'])
@permission_classes([IsAdmin])
def create_user(request):
    serializer = CreateUserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAdmin])
def list_users(request):
    users = User.objects.all()
    return Response(UserSerializer(users, many=True).data)

@api_view(['PATCH'])
@permission_classes([IsAdmin])
def update_user_role(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        user.role = request.data.get('role', user.role)
        user.save()
        return Response(UserSerializer(user).data)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PATCH'])
@permission_classes([IsAdmin])
def toggle_user_status(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        user.is_active = not user.is_active
        user.save()
        return Response(UserSerializer(user).data)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAdmin])
def reset_password(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        new_password = request.data.get('password')
        user.set_password(new_password)
        user.save()
        return Response({'message': 'Password reset successful'})
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_tickets(request):
    sync_service = ZammadSyncService()
    count = sync_service.sync_new_tickets()
    return Response({'synced': count})

@api_view(['GET'])
@permission_classes([AllowAny])  # Changé de IsAuthenticated à AllowAny
def list_tickets(request):
    api = ZammadAPIService()
    tickets = api.get_tickets()
    return Response(tickets)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_ticket_processed(request, ticket_id):
    try:
        ticket = Ticket.objects.get(zammad_id=ticket_id)
        ticket.processed = True
        ticket.save()
        return Response({'message': 'Ticket marqué comme traité'})
    except Ticket.DoesNotExist:
        return Response({'error': 'Ticket non trouvé'}, status=404)
# Ajout aux views.py
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_ticket(request, ticket_id):
    """Analyser un ticket avec l'IA"""
    try:
        ticket = Ticket.objects.get(zammad_id=ticket_id)
        analyzer = TicketAnalyzerService()
        result = analyzer.analyze_ticket(ticket)
        
        if result['success']:
            return Response({
                'message': 'Analyse terminée',
                'analysis': TicketAnalysisSerializer(result['analysis']).data
            })
        else:
            return Response({'error': result['error']}, status=400)
            
    except Ticket.DoesNotExist:
        return Response({'error': 'Ticket non trouvé'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def publish_analysis(request, analysis_id):
    """Publier une analyse sur Zammad"""
    try:
        analysis = TicketAnalysis.objects.get(id=analysis_id)
        analyzer = TicketAnalyzerService()
        result = analyzer.publish_to_zammad(analysis)
        
        return Response(result)
        
    except TicketAnalysis.DoesNotExist:
        return Response({'error': 'Analyse non trouvée'}, status=404)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pending_analyses(request):
    """Lister les analyses en attente de validation"""
    analyses = TicketAnalysis.objects.filter(
        publish_mode='suggestion',
        published=False
    ).select_related('ticket')
    
    return Response(TicketAnalysisSerializer(analyses, many=True).data)

from .models import TicketAnalysis
from .serializers import TicketAnalysisSerializer

@api_view(['GET'])
@permission_classes([AllowAny])  # Changé de IsAuthenticated à AllowAny
def ticket_detail(request, ticket_id):
    api = ZammadAPIService()
    ticket = api.get_ticket_details(ticket_id)
    articles = api.get_ticket_articles(ticket_id)
    return Response({
        'ticket': ticket,
        'articles': articles
    })
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_ai_response(request, analysis_id):
    try:
        analysis = TicketAnalysis.objects.get(id=analysis_id)
        analysis.ai_response = request.data.get('ai_response', analysis.ai_response)
        analysis.save()
        return Response(TicketAnalysisSerializer(analysis).data)
    except TicketAnalysis.DoesNotExist:
        return Response({'error': 'Analyse non trouvée'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_response(request, analysis_id):
    try:
        analysis = TicketAnalysis.objects.get(id=analysis_id)
        analysis.published = True
        analysis.save()
        return Response({'message': 'Réponse validée'})
    except TicketAnalysis.DoesNotExist:
        return Response({'error': 'Analyse non trouvée'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_to_zammad(request, analysis_id):
    try:
        analysis = TicketAnalysis.objects.get(id=analysis_id)
        # Logique d'envoi vers Zammad
        return Response({'message': 'Envoyé vers Zammad'})
    except TicketAnalysis.DoesNotExist:
        return Response({'error': 'Analyse non trouvée'}, status=404)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ticket_detail(request, ticket_id):
    api = ZammadAPIService()
    ticket = api.get_ticket_details(ticket_id)
    articles = api.get_ticket_articles(ticket_id)
    return Response({
        'ticket': ticket,
        'articles': articles
    })

@api_view(['GET', 'POST'])  # Ajouté GET
@permission_classes([AllowAny])  # Changé de IsAuthenticated à AllowAny
def analyze_ticket_from_zammad(request, ticket_id):
    try:
        # Get ticket from Zammad
        api = ZammadAPIService()
        ticket_data = api.get_ticket_details(ticket_id)
        articles = api.get_ticket_articles(ticket_id)
        
        # Create or get ticket in database
        ticket, created = Ticket.objects.get_or_create(
            zammad_id=ticket_data['id'],
            defaults={
                'title': ticket_data['title'],
                'body': articles[0]['body'] if articles else '',
                'status': 'open',
                'customer_email': '',
                'created_at': timezone.now(),
                'updated_at': timezone.now()
            }
        )
        
        # Analyze with AI
        from .services.ticket_analyzer import TicketAnalyzerService
        analyzer = TicketAnalyzerService()
        result = analyzer.analyze_ticket(ticket)
        
        return Response(result)  # Retourner directement result
            
    except Exception as e:
        return Response({'error': str(e)}, status=400)