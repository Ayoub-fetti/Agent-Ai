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
import logging
import uuid
import threading
from .services.knowledge_base_service import KnowledgeBaseService


logger = logging.getLogger(__name__)


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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_internal_article(request, ticket_id):
    try:
        api = ZammadAPIService()
        subject = request.data.get('subject', 'Note d\'analyse IA')
        body = request.data.get('body', '')
        
        result = api.create_internal_article(ticket_id, subject, body)
        return Response({'message': 'Article interne créé', 'article': result})
    except Exception as e:
        return Response({'error': str(e)}, status=400)

# ==================== LEADS API ====================

from .models import Lead
from .serializers import LeadSerializer, LeadSearchRequestSerializer
from .services.lead_service import LeadService
from .services.search_progress import create_tracker, get_tracker, remove_tracker

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_leads(request):
    """Lance une recherche de leads GTB/GTEB avec progression"""
    try:
        serializer = LeadSearchRequestSerializer(data=request.data)
        if serializer.is_valid():
            countries = serializer.validated_data.get('countries', ['Maroc', 'France', 'Canada'])
            max_leads = serializer.validated_data.get('max_leads_per_source', 50)
            
            # Créer un ID de recherche unique
            search_id = str(uuid.uuid4())
            
            # Créer un tracker de progression
            progress_tracker = create_tracker(search_id)
            
            # Lancer la recherche dans un thread séparé
            def run_search():
                try:
                    lead_service = LeadService()
                    # Rechercher et traiter les leads avec progression
                    results = lead_service.search_and_create_leads(
                        countries=countries,
                        max_leads_per_source=max_leads,
                        progress_tracker=progress_tracker
                    )
                    
                    # Stocker les résultats dans le tracker
                    progress_tracker.search_results = results
                except Exception as e:
                    logger.error(f"Erreur recherche: {e}")
                    progress_tracker.error(str(e))
            
            # Démarrer le thread
            thread = threading.Thread(target=run_search)
            thread.daemon = True
            thread.start()
            
            return Response({
                'search_id': search_id,
                'message': 'Recherche lancée',
                'status': 'running'
            })
        return Response(serializer.errors, status=400)
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_progress(request, search_id):
    """Récupère la progression d'une recherche"""
    try:
        tracker = get_tracker(search_id)
        if not tracker:
            return Response({'error': 'Recherche non trouvée'}, status=404)
        
        progress = tracker.get_progress()
        
        # Si terminée, inclure les résultats
        if progress['status'] == 'completed' and hasattr(tracker, 'search_results'):
            progress['results'] = tracker.search_results
            # Nettoyer après 5 minutes
            remove_tracker(search_id)
        
        return Response(progress)
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_leads(request):
    """Liste tous les leads avec filtres"""
    try:
        leads = Lead.objects.all()
        
        # Filtres
        temperature = request.query_params.get('temperature')
        if temperature:
            leads = leads.filter(temperature=temperature)
        
        country = request.query_params.get('country')
        if country:
            leads = leads.filter(country=country)
        
        project_type = request.query_params.get('project_type')
        if project_type:
            leads = leads.filter(project_type=project_type)
        
        sector = request.query_params.get('sector')
        if sector:
            leads = leads.filter(sector=sector)
        
        min_score = request.query_params.get('min_score')
        if min_score:
            try:
                leads = leads.filter(score__gte=int(min_score))
            except ValueError:
                pass
        
        is_contacted = request.query_params.get('is_contacted')
        if is_contacted is not None:
            leads = leads.filter(is_contacted=is_contacted.lower() == 'true')
        
        # Tri
        ordering = request.query_params.get('ordering', '-score')
        leads = leads.order_by(ordering)
        
        # Pagination
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        total = leads.count()
        leads_page = leads[start:end]
        
        serializer = LeadSerializer(leads_page, many=True)
        
        return Response({
            'count': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lead_detail(request, lead_id):
    """Détails d'un lead"""
    try:
        lead = Lead.objects.get(id=lead_id)
        serializer = LeadSerializer(lead)
        return Response(serializer.data)
    except Lead.DoesNotExist:
        return Response({'error': 'Lead non trouvé'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reanalyze_lead(request, lead_id):
    """Réanalyse un lead existant"""
    try:
        lead_service = LeadService()
        result = lead_service.reanalyze_lead(lead_id)
        
        if result.get('success'):
            return Response(result)
        else:
            return Response(result, status=400)
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_lead(request, lead_id):
    """Met à jour un lead"""
    try:
        lead = Lead.objects.get(id=lead_id)
        
        # Champs modifiables
        updatable_fields = ['is_contacted', 'is_converted', 'notes', 'email', 'phone']
        for field in updatable_fields:
            if field in request.data:
                setattr(lead, field, request.data[field])
        
        lead.save()
        serializer = LeadSerializer(lead)
        return Response(serializer.data)
    except Lead.DoesNotExist:
        return Response({'error': 'Lead non trouvé'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def leads_stats(request):
    """Statistiques sur les leads"""
    try:
        total = Lead.objects.count()
        by_temperature = {
            'chaud': Lead.objects.filter(temperature='chaud').count(),
            'tiede': Lead.objects.filter(temperature='tiede').count(),
            'froid': Lead.objects.filter(temperature='froid').count()
        }
        by_country = {}
        for country in Lead.objects.values_list('country', flat=True).distinct():
            by_country[country] = Lead.objects.filter(country=country).count()
        
        by_project_type = {}
        for pt in Lead.objects.values_list('project_type', flat=True).distinct():
            if pt:
                by_project_type[pt] = Lead.objects.filter(project_type=pt).count()
        
        contacted = Lead.objects.filter(is_contacted=True).count()
        converted = Lead.objects.filter(is_converted=True).count()
        
        avg_score = Lead.objects.aggregate(avg_score=models.Avg('score'))['avg_score'] or 0
        
        return Response({
            'total': total,
            'by_temperature': by_temperature,
            'by_country': by_country,
            'by_project_type': by_project_type,
            'contacted': contacted,
            'converted': converted,
            'conversion_rate': (converted / total * 100) if total > 0 else 0,
            'avg_score': round(avg_score, 2)
        })
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['GET'])
@permission_classes([IsAdmin])
def dashboard_stats(request):
    """Statistiques du tableau de bord admin"""
    try:
        # User stats
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        inactive_users = total_users - active_users
        
        users_by_role = {
            'ADMIN': User.objects.filter(role='ADMIN').count(),
            'AGENT TECHNIQUE': User.objects.filter(role='AGENT TECHNIQUE').count(),
            'AGENT COMMERCIAL': User.objects.filter(role='AGENT COMMERCIAL').count(),
        }
        
        # Leads stats
        total_leads = Lead.objects.count()
        leads_by_temperature = {
            'chaud': Lead.objects.filter(temperature='chaud').count(),
            'tiede': Lead.objects.filter(temperature='tiede').count(),
            'froid': Lead.objects.filter(temperature='froid').count(),
        }
        converted_leads = Lead.objects.filter(is_converted=True).count()
        
        # Tickets stats (from database)
        total_tickets = Ticket.objects.count()
        processed_tickets = Ticket.objects.filter(processed=True).count()
        pending_tickets = total_tickets - processed_tickets
        
        # Recent activity
        recent_users = User.objects.order_by('-date_joined')[:5].values('id', 'username', 'role', 'date_joined', 'is_active')
        recent_leads = Lead.objects.order_by('-created_at')[:5].values('id', 'organization_name', 'temperature', 'score', 'created_at')
        
        return Response({
            'users': {
                'total': total_users,
                'active': active_users,
                'inactive': inactive_users,
                'by_role': users_by_role,
                'recent': list(recent_users),
            },
            'leads': {
                'total': total_leads,
                'by_temperature': leads_by_temperature,
                'converted': converted_leads,
                'conversion_rate': round((converted_leads / total_leads * 100), 2) if total_leads > 0 else 0,
                'recent': list(recent_leads),
            },
            'tickets': {
                'total': total_tickets,
                'processed': processed_tickets,
                'pending': pending_tickets,
            }
        })
    except Exception as e:
        return Response({'error': str(e)}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_knowledge_article(request):
    """Créer un article dans la base de connaissance"""
    try:
        kb_service = KnowledgeBaseService()
        
        title = request.data.get('title')
        content = request.data.get('content')
        category = request.data.get('category', 'Procédures Internes')
        knowledge_base_id = request.data.get('knowledge_base_id', 1)
        
        if not title or not content:
            return Response({'error': 'Titre et contenu requis'}, status=400)
        
        result = kb_service.create_knowledge_article(
            title=title,
            content=content,
            category=category,
            knowledge_base_id=knowledge_base_id
        )
        
        return Response(result)
        
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def suggest_kb_article_from_ticket(request, ticket_id):
    """Suggérer un article KB basé sur un ticket"""
    try:
        ticket = Ticket.objects.get(zammad_id=ticket_id)
        
        # Récupérer l'analyse existante
        if hasattr(ticket, 'analysis'):
            analysis_data = {
                'category': ticket.analysis.category,
                'priority_label': ticket.analysis.get_priority_display(),
                'ai_response': {'solution_steps': []}  # Simplifier pour l'exemple
            }
        else:
            return Response({'error': 'Ticket non analysé'}, status=400)
        
        ticket_data = {
            'title': ticket.title,
            'body': ticket.body,
            'status': ticket.status
        }
        
        kb_service = KnowledgeBaseService()
        suggestion = kb_service.suggest_knowledge_article(analysis_data, ticket_data)
        
        return Response(suggestion)
        
    except Ticket.DoesNotExist:
        return Response({'error': 'Ticket non trouvé'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=400)


from django.db import models
# Ajout rker-index=1 reference-tracker>à la fin de views.py

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_knowledge_article(request):
    """Créer un article dans la base de connaissance"""
    try:
        from .services.zammad_api import ZammadAPIService
        
        title = request.data.get('title')
        content = request.data.get('content')
        category = request.data.get('category', 'Procédures Internes')
        
        if not title or not content:
            return Response({'error': 'Titre et contenu requis'}, status=400)
        
        zammad_api = ZammadAPIService()
        
        # Créer l'article dans Zammad (KB ID par défaut = 1)
        result = zammad_api.create_knowledge_base_answer(
            knowledge_base_id=1,
            title=title,
            content=content,
            internal=True
        )
        
        return Response({
            'success': True,
            'message': 'Article créé avec succès',
            'article': result
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def suggest_kb_article_from_ticket(request, ticket_id):
    """Suggérer un article KB basé sur un ticket"""
    try:
        from .services.llm_client import LLMClient
        
        # Récupérer les données du ticket depuis Zammad
        api = ZammadAPIService()
        ticket_data = api.get_ticket_details(ticket_id)
        
        # Générer une suggestion avec l'IA
        llm_client = LLMClient()
        
        prompt = f"""
        Analyse ce ticket et détermine s'il mérite un article de base de connaissance.

        TICKET:
        - Titre: {ticket_data.get('title', '')}
        - Contenu: {ticket_data.get('body', '')}

        CRITÈRES pour créer un article:
        - Problème technique récurrent
        - Solution réutilisable
        - Procédure importante

        RÉPONDS EN JSON:
        {{
            "should_create": true/false,
            "reason": "Raison de la décision",
            "title": "Titre de l'article si recommandé",
            "content": "<p>Contenu HTML détaillé avec solution</p>",
            "category": "Procédures Internes"
        }}
        """
        
        result = llm_client.call_api(prompt, "Tu es un expert en documentation. Réponds uniquement en JSON.")
        
        if not result.get('success'):
            return Response({'error': 'Erreur IA'}, status=400)
        
        # Parser la réponse
        import json
        try:
            suggestion = json.loads(result['content'].strip().replace('```json', '').replace('```', ''))
        except:
            suggestion = {
                "should_create": False,
                "reason": "Impossible d'analyser le ticket",
                "title": "",
                "content": "",
                "category": "Procédures Internes"
            }
        
        return Response({'suggestion': suggestion})
        
    except Exception as e:
        return Response({'error': str(e)}, status=400)

