import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_commerce.settings')
django.setup()

from accounts.models import Utilisateur

# Compte GESTIONNAIRE
if not Utilisateur.objects.filter(username='employe').exists():
    Utilisateur.objects.create_superuser(
        username='employe',
        email='employe@ibrafrik.com',
        password='Employe1234!',
        role='GESTIONNAIRE',
        first_name='Abdoul',
        last_name='Aziz'
    )
    print('✅ Gestionnaire créé !')
else:
    print('ℹ️ Gestionnaire existe déjà.')

# Compte ADMIN
if not Utilisateur.objects.filter(username='chef').exists():
    Utilisateur.objects.create_superuser(
        username='chef',
        email='chef@ibrafrik.com',
        password='Chef1234!',
        role='ADMIN',
        first_name='Chef',
        last_name='Entreprise'
    )
    print('✅ Admin créé !')
else:
    print('ℹ️ Admin existe déjà.')