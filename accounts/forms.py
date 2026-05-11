from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from .models import Utilisateur


class ProfilForm(forms.ModelForm):
    class Meta:
        model  = Utilisateur
        fields = ['first_name', 'last_name', 'email', 'username', 'photo']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control'}),
            'username':   forms.TextInput(attrs={'class': 'form-control'}),
            'photo':      forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
        labels = {
            'first_name': 'Prénom',
            'last_name':  'Nom',
            'email':      'Adresse email',
            'username':   'Identifiant',
            'photo':      'Photo de profil',
        }


class ChangerMotDePasseForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget = forms.PasswordInput(
            attrs={'class': 'form-control',
                   'placeholder': 'Mot de passe actuel'}
        )
        self.fields['new_password1'].widget = forms.PasswordInput(
            attrs={'class': 'form-control',
                   'placeholder': 'Nouveau mot de passe'}
        )
        self.fields['new_password2'].widget = forms.PasswordInput(
            attrs={'class': 'form-control',
                   'placeholder': 'Confirmer le nouveau mot de passe'}
        )
        self.fields['old_password'].label  = 'Mot de passe actuel'
        self.fields['new_password1'].label = 'Nouveau mot de passe'
        self.fields['new_password2'].label = 'Confirmation'