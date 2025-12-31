# Guide d'utilisation du système de leads GTB/GTEB

## 🎯 Vue d'ensemble

Le système permet aux agents commerciaux de trouver automatiquement des leads commerciaux spécifiques à la GTB (Gestion Technique du Bâtiment) et GTEB (Génie Technique Électrique du Bâtiment).

## 📋 Fonctionnalités

### Backend

1. **Recherche automatique de leads**
   - Marchés publics (Maroc, France, Canada)
   - Entreprises GTB/GTEB
   - Offres d'emploi (indicateurs de besoin)

2. **Normalisation des données**
   - Nettoyage et unification des noms d'entreprises
   - Standardisation des villes et pays
   - Détection automatique du type de projet

3. **Enrichissement**
   - Identification du secteur d'activité
   - Estimation de la taille de l'entreprise
   - Extraction d'emails professionnels

4. **Scoring IA**
   - Score de 0 à 100 basé sur plusieurs critères
   - Classification automatique : Froid (0-39), Tiède (40-69), Chaud (70-100)
   - Justification claire du score

### Frontend

- Dashboard avec statistiques et graphiques
- Liste des leads avec filtres avancés
- Détails complets de chaque lead
- Actions : marquer comme contacté, réanalyser, convertir

## 🚀 Utilisation

### 1. Lancer une recherche de leads

**Via l'interface web :**
1. Connectez-vous en tant qu'agent commercial
2. Cliquez sur "Rechercher des leads"
3. Sélectionnez les pays à rechercher
4. Cliquez sur "Lancer la recherche"

**Via la ligne de commande :**
```bash
cd backend
source venv/bin/activate
unset DEBUG  # Si nécessaire
python manage.py test_leads
```

### 2. Consulter les leads

**Via l'interface web :**
- Accédez au dashboard commercial
- Utilisez les filtres pour affiner votre recherche
- Cliquez sur un lead pour voir les détails

**Via l'API REST :**
```bash
# Lister tous les leads
GET /api/leads/

# Filtrer par température
GET /api/leads/?temperature=chaud

# Filtrer par pays
GET /api/leads/?country=Maroc

# Filtrer par score minimum
GET /api/leads/?min_score=70

# Obtenir les statistiques
GET /api/leads/stats/
```

### 3. Gérer un lead

- **Marquer comme contacté** : Cliquez sur le lead et utilisez le bouton "Marquer comme contacté"
- **Réanalyser** : Utilisez le bouton "Réanalyser" pour recalculer le score
- **Ajouter des notes** : Modifiez le lead pour ajouter des notes personnelles

## 📊 Critères de scoring

Le score (0-100) est calculé selon :

1. **Projet GTB/GTEB explicite** (0-30 points)
   - Projet GTB/GTEB identifié : +30
   - Projet mixte : +25
   - Projet CVC/Supervision/Électricité : +15
   - Mots-clés GTB détectés : +10

2. **Marché public** (0-25 points)
   - Marché public identifié : +25
   - Budget > 1M : +5
   - Budget > 100K : +3
   - Marché récent (<30 jours) : +5
   - Marché récent (<90 jours) : +3

3. **Offre d'emploi GTB** (0-20 points)
   - Offre d'emploi active : +20

4. **Taille de l'entreprise** (0-15 points)
   - Grande entreprise : +15
   - Moyenne : +10
   - Petite : +5

5. **Informations complètes** (0-10 points)
   - Email : +3
   - Téléphone : +2
   - Site web : +2
   - Description : +3

6. **Secteur d'activité** (0-10 points)
   - Hôpital/Industrie/Public : +10
   - Tertiaire : +5

## 🔧 Configuration

### Variables d'environnement

Pour éviter les conflits avec la variable `DEBUG` du système, utilisez `DJANGO_DEBUG` dans votre fichier `.env` :

```env
DJANGO_DEBUG=True
SECRET_KEY=votre-secret-key
DB_NAME=agent_ai
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
OPEN_ROUTER_API_KEY=votre-api-key
```

### Exécuter les migrations

```bash
cd backend
source venv/bin/activate
unset DEBUG  # Si nécessaire
python manage.py migrate
```

## 📝 Endpoints API

### Recherche
- `POST /api/leads/search/` - Lancer une recherche de leads

### Consultation
- `GET /api/leads/` - Lister les leads (avec filtres)
- `GET /api/leads/stats/` - Statistiques
- `GET /api/leads/<id>/` - Détails d'un lead

### Gestion
- `POST /api/leads/<id>/reanalyze/` - Réanalyser un lead
- `PATCH /api/leads/<id>/update/` - Mettre à jour un lead

## 🎨 Interface Admin Django

Le modèle `Lead` est enregistré dans l'admin Django avec :
- Filtres par température, pays, type de projet, secteur
- Recherche par nom d'organisation, titre, description
- Affichage des champs importants
- Édition complète des leads

Accès : `/admin/` (nécessite les droits admin)

## 🔮 Prochaines étapes

1. **Connecter les vraies APIs**
   - BOAMP (France)
   - Portails marocains/canadiens
   - Google Maps/Places API

2. **Automatisation**
   - Tâches périodiques (Celery) pour recherche automatique
   - Notifications pour nouveaux leads chauds

3. **Améliorations**
   - Extraction d'emails plus avancée
   - Intégration avec CRM
   - Export des leads

## 🐛 Dépannage

### Problème avec la variable DEBUG

Si vous rencontrez l'erreur `ValueError: Invalid truth value: warn`, c'est que la variable d'environnement `DEBUG` est définie à "WARN" (pour le logging).

**Solution :**
```bash
unset DEBUG
python manage.py [commande]
```

Ou utilisez `DJANGO_DEBUG` dans votre `.env` au lieu de `DEBUG`.

### Module bs4 non trouvé

```bash
cd backend
source venv/bin/activate
pip install beautifulsoup4 unidecode
```

## 📞 Support

Pour toute question ou problème, consultez les logs Django ou contactez l'équipe de développement.

