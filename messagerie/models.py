from django.db import models
from django.conf import settings

class Message(models.Model):
    expediteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messages_envoyes')
    destinataire = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messages_recus')
    contenu = models.TextField()
    date_envoi = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)

    def __str__(self):
        return f"De {self.expediteur} à {self.destinataire} — {self.date_envoi.date()}"

    class Meta:
        verbose_name = 'Message'
        ordering = ['-date_envoi']