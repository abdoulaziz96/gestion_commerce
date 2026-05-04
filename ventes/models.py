from django.db import models
from django.conf import settings
from produits.models import Produit

class Vente(models.Model):
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT, related_name='ventes')
    gestionnaire = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='ventes')
    quantite = models.IntegerField()
    prix_unitaire = models.DecimalField(max_digits=12, decimal_places=2)
    montant_total = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    date_vente = models.DateTimeField(auto_now_add=True)
    client = models.CharField(max_length=200, blank=True)
    annulee = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.montant_total = self.quantite * self.prix_unitaire
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Vente {self.id} — {self.produit.nom} ({self.date_vente.date()})"

    class Meta:
        verbose_name = 'Vente'
        ordering = ['-date_vente']