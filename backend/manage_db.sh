#!/bin/bash

# Créer environnement virtuel
python3 -m venv venv

# Activer environnement virtuel
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer la base de données PostgreSQL
python setup_db.py

# Créer les migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Créer le superuser
python manage.py createsuperuser --username admin --email admin@agent-ai.com

echo "Configuration terminée!"
echo "Pour réactiver l'environnement: source venv/bin/activate"
