from django import forms
from .models import Vente
from produits.models import Produit


class VenteForm(forms.ModelForm):
    class Meta:
        model = Vente
        fields = ['produit', 'quantite', 'prix_unitaire', 'client']
        widgets = {
            'produit':       forms.Select(attrs={'class': 'form-select'}),
            'quantite':      forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'prix_unitaire': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'client':        forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optionnel'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['produit'].queryset = Produit.objects.filter(actif=True)

    def clean(self):
        cleaned_data = super().clean()
        produit  = cleaned_data.get('produit')
        quantite = cleaned_data.get('quantite')
        if produit and quantite:
            if quantite > produit.quantite_stock:
                raise forms.ValidationError(
                    f"Stock insuffisant. Disponible : {produit.quantite_stock}"
                )
        return cleaned_data