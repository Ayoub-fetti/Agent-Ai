# backend/core/services/search_progress.py
"""
Service pour gérer la progression des recherches de leads
"""
import threading
from typing import Dict, Any, Callable, Optional
from datetime import datetime

class SearchProgressTracker:
    """Tracker pour suivre la progression d'une recherche"""
    
    def __init__(self, search_id: str):
        self.search_id = search_id
        self.total_sources = 0
        self.completed_sources = 0
        self.current_source = ""
        self.leads_found = 0
        self.errors = []
        self.status = "pending"  # pending, running, completed, error
        self.start_time = None
        self.end_time = None
        self.callback: Optional[Callable] = None
        self._lock = threading.Lock()
    
    def set_total_sources(self, total: int):
        """Définit le nombre total de sources à consulter"""
        with self._lock:
            self.total_sources = total
    
    def start(self):
        """Démarre le tracking"""
        with self._lock:
            self.status = "running"
            self.start_time = datetime.now()
        self._notify()
    
    def update(self, source_name: str, leads_count: int = 0, error: Optional[str] = None):
        """Met à jour la progression"""
        with self._lock:
            # Validation pour éviter le dépassement
            if self.completed_sources >= self.total_sources:
                return
            
            self.current_source = source_name
            # Compter toutes les sources (avec ou sans erreur) comme complétées
            self.completed_sources += 1
            
            if error:
                self.errors.append({'source': source_name, 'error': error})
            else:
                self.leads_found += leads_count
        self._notify()

    
    def complete(self):
        """Marque la recherche comme terminée"""
        with self._lock:
            self.status = "completed"
            self.end_time = datetime.now()
        self._notify()
    
    def error(self, error_message: str):
        """Marque la recherche comme en erreur"""
        with self._lock:
            self.status = "error"
            self.end_time = datetime.now()
            self.errors.append({'source': 'global', 'error': error_message})
        self._notify()
    
    def get_progress(self) -> Dict[str, Any]:
        """Retourne l'état actuel de la progression"""
        with self._lock:
            percentage = 0
            if self.total_sources > 0:
                percentage = int((self.completed_sources / self.total_sources) * 100)
            
            elapsed = None
            if self.start_time:
                end = self.end_time or datetime.now()
                elapsed = (end - self.start_time).total_seconds()
            
            result = {
                'search_id': self.search_id,
                'status': self.status,
                'percentage': min(percentage, 100),
                'current_source': self.current_source,
                'completed_sources': self.completed_sources,
                'total_sources': self.total_sources,
                'leads_found': self.leads_found,
                'errors': self.errors,
                'elapsed_seconds': elapsed
            }
            
            # Ajouter les résultats si disponibles
            if hasattr(self, 'search_results'):
                result['results'] = self.search_results
            
            return result
    
    def set_callback(self, callback: Callable):
        """Définit un callback pour les notifications"""
        self.callback = callback
    
    def _notify(self):
        """Notifie le callback si défini"""
        if self.callback:
            try:
                self.callback(self.get_progress())
            except Exception as e:
                print(f"Erreur notification callback: {e}")

# Stockage global des trackers (en production, utiliser Redis ou une base de données)
_active_trackers: Dict[str, SearchProgressTracker] = {}
_trackers_lock = threading.Lock()

def get_tracker(search_id: str) -> Optional[SearchProgressTracker]:
    """Récupère un tracker par son ID"""
    with _trackers_lock:
        return _active_trackers.get(search_id)

def create_tracker(search_id: str) -> SearchProgressTracker:
    """Crée un nouveau tracker"""
    tracker = SearchProgressTracker(search_id)
    with _trackers_lock:
        _active_trackers[search_id] = tracker
    return tracker

def remove_tracker(search_id: str):
    """Supprime un tracker"""
    with _trackers_lock:
        _active_trackers.pop(search_id, None)

