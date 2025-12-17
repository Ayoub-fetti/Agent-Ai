#!/usr/bin/env python3
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from decouple import config
import sys

def setup_database():
    try:
        conn = psycopg2.connect(
            host=config('DB_HOST', default='localhost'),
            port=config('DB_PORT', default='5432'),
            user='postgres',
            password=input('Mot de passe PostgreSQL admin: ')
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        db_name = config('DB_NAME')
        db_user = config('DB_USER')
        db_password = config('DB_PASSWORD')
        
        # Créer l'utilisateur (ignorer si existe)
        try:
            cursor.execute(f"CREATE USER {db_user} WITH PASSWORD '{db_password}';")
            print(f"Utilisateur {db_user} créé")
        except psycopg2.errors.DuplicateObject:
            print(f"Utilisateur {db_user} existe déjà")
        
        # Créer la base de données (ignorer si existe)
        try:
            cursor.execute(f"CREATE DATABASE {db_name} OWNER {db_user};")
            print(f"Base de données {db_name} créée")
        except psycopg2.errors.DuplicateDatabase:
            print(f"Base de données {db_name} existe déjà")
        
        # Accorder les privilèges
        cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};")
        print("Privilèges accordés")
        
        cursor.close()
        conn.close()
        print("Configuration terminée avec succès!")
        
    except Exception as e:
        print(f"Erreur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_database()
