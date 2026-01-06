from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Create admin user'

    def handle(self, *args, **options):
        User = get_user_model()
        email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
        password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        if not User.objects.filter(email=email).exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email=email,
                password=password
            )
            admin_user.role = User.Role.ADMIN
            admin_user.save()
            self.stdout.write(f'Admin créé avec rôle ADMIN: {email}')
        else:
            # Mettre à jour le rôle si l'utilisateur existe déjà
            admin_user = User.objects.get(email=email)
            admin_user.role = User.Role.ADMIN
            admin_user.save()
            self.stdout.write('Admin existe déjà - rôle mis à jour')
