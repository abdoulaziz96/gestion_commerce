from django import forms
from .models import Produit, Categorie


class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = [
            'nom', 'categorie', 'description',
            'prix_achat', 'prix_vente',
            'quantite_stock', 'seuil_alerte',
            'image', 'actif'
        ]
        widgets = {
            'nom':            forms.TextInput(attrs={'class': 'form-control'}),
            'categorie':      forms.Select(attrs={'class': 'form-select'}),
            'description':    forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'prix_achat':     forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'prix_vente':     forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantite_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'seuil_alerte':   forms.NumberInput(attrs={'class': 'form-control'}),
            'image':          forms.FileInput(attrs={'class': 'form-control'}),
            'actif':          forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CategorieForm(forms.ModelForm):
    class Meta:
        model = Categorie
        fields = ['nom', 'description']
        widgets = {
            'nom':         forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }