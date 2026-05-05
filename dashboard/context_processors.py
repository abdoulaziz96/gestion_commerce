from messagerie.models import Message


def messages_non_lus(request):
    if request.user.is_authenticated:
        count = Message.objects.filter(
            destinataire=request.user, lu=False
        ).count()
        return {'messages_non_lus_count': count}
    return {'messages_non_lus_count': 0}