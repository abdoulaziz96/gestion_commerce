from django import forms
from .models import Depense


class DepenseForm(forms.ModelForm):
    class Meta:
        model = Depense
        fields = ['libelle', 'categorie_depense', 'montant', 'date_depense', 'justificatif']
        widgets = {
            'libelle':           forms.TextInput(attrs={'class': 'form-control'}),
            'categorie_depense': forms.TextInput(attrs={'class': 'form-control',
                                                        'placeholder': 'Ex: loyer, transport...'}),
            'montant':           forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'date_depense':      forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'justificatif':      forms.FileInput(attrs={'class': 'form-control'}),
        }