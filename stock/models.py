from django.db import models
from django.conf import settings
from produits.models import Produit

class MouvementStock(models.Model):
    ENTREE = 'ENTREE'
    SORTIE = 'SORTIE'
    AJUSTEMENT = 'AJUSTEMENT'
    TYPE_CHOICES = [
        (ENTREE, 'Entrée'),
        (SORTIE, 'Sortie'),
        (AJUSTEMENT, 'Ajustement'),
    ]

    produit = models.ForeignKey(Produit, on_delete=models.PROTECT, related_name='mouvements')
    type_mouvement = models.CharField(max_length=20, choices=TYPE_CHOICES)
    quantite = models.IntegerField()
    motif = models.CharField(max_length=255)
    gestionnaire = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='mouvements_stock')
    date_mouvement = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_type_mouvement_display()} — {self.produit.nom} ({self.quantite})"

    class Meta:
        verbose_name = 'Mouvement de stock'
        ordering = ['-date_mouvement']