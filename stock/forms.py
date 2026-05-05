from django import forms
from produits.models import Produit


class EntreeStockForm(forms.Form):
    produit  = forms.ModelChoiceField(
        queryset=Produit.objects.filter(actif=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    quantite = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    motif    = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Réapprovisionnement fournisseur'
        })
    )


class SortieStockForm(forms.Form):
    produit  = forms.ModelChoiceField(
        queryset=Produit.objects.filter(actif=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    quantite = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    motif    = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Perte, casse, ajustement'
        })
    )


class InventaireForm(forms.Form):
    def __init__(self, *args, produits=None, **kwargs):
        super().__init__(*args, **kwargs)
        if produits:
            for produit in produits:
                self.fields[f'stock_{produit.pk}'] = forms.IntegerField(
                    min_value=0,
                    initial=produit.quantite_stock,
                    required=False,
                    widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm'})
                )