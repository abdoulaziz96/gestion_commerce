from django import forms
from .models import Message
from accounts.models import Utilisateur


class MessageForm(forms.ModelForm):
    class Meta:
        model  = Message
        fields = ['destinataire', 'contenu']
        widgets = {
            'destinataire': forms.Select(attrs={'class': 'form-select'}),
            'contenu':      forms.Textarea(attrs={
                'class': 'form-control',
                'rows':  5,
                'placeholder': 'Écrivez votre message ici...'
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            # Ne pas s'envoyer un message à soi-même
            self.fields['destinataire'].queryset = Utilisateur.objects.filter(
                is_active=True
            ).exclude(pk=user.pk)