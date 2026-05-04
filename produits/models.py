from django.db import models

class Categorie(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = 'Catégorie'

class Produit(models.Model):
    nom = models.CharField(max_length=200)
    categorie = models.ForeignKey(Categorie, on_delete=models.PROTECT, related_name='produits')
    description = models.TextField(blank=True)
    prix_achat = models.DecimalField(max_digits=12, decimal_places=2)
    prix_vente = models.DecimalField(max_digits=12, decimal_places=2)
    quantite_stock = models.IntegerField(default=0)
    seuil_alerte = models.IntegerField(default=5)
    image = models.ImageField(upload_to='produits/', blank=True, null=True)
    date_ajout = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)

    def __str__(self):
        return self.nom

    @property
    def marge(self):
        return self.prix_vente - self.prix_achat

    @property
    def en_alerte(self):
        return self.quantite_stock <= self.seuil_alerte

    class Meta:
        verbose_name = 'Produit'