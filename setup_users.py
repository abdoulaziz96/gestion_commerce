import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_commerce.settings')
django.setup()

from accounts.models import Utilisateur

# Chef ADMIN
u, _ = Utilisateur.objects.get_or_create(username='chef')
u.set_password('Chef2026!')
u.role = 'ADMIN'
u.is_active = True
u.is_staff = True
u.is_superuser = True
u.save()
print('chef OK')

# Employe GESTIONNAIRE
e, _ = Utilisateur.objects.get_or_create(username='employe')
e.set_password('Employe2026!')
e.role = 'GESTIONNAIRE'
e.is_active = True
e.save()
print('employe OK')