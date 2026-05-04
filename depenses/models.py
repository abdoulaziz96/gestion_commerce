from django.db import models
from django.conf import settings

class Depense(models.Model):
    libelle = models.CharField(max_length=200)
    categorie_depense = models.CharField(max_length=100)
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    gestionnaire = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='depenses')
    date_depense = models.DateField()
    justificatif = models.FileField(upload_to='justificatifs/', blank=True, null=True)

    def __str__(self):
        return f"{self.libelle} — {self.montant} FCFA"

    class Meta:
        verbose_name = 'Dépense'
        ordering = ['-date_depense']