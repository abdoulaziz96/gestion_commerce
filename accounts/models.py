from django.contrib.auth.models import AbstractUser
from django.db import models

class Utilisateur(AbstractUser):
    GESTIONNAIRE = 'GESTIONNAIRE'
    ADMIN = 'ADMIN'
    ROLE_CHOICES = [
        (GESTIONNAIRE, 'Gestionnaire'),
        (ADMIN, 'Administrateur'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=GESTIONNAIRE,
    )

    def is_gestionnaire(self):
        return self.role == self.GESTIONNAIRE

    def is_admin_bc(self):
        return self.role == self.ADMIN

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"