from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from ventes.models import Vente
from depenses.models import Depense
from django.utils import timezone


@login_required
def statut_sync(request):
    # Ventes annulées exclues du comptage
    ventes_recentes   = Vente.objects.filter(annulee=False).count()
    depenses_recentes = Depense.objects.all().count()

    return JsonResponse({
        'synced':       True,
        'ventes':       ventes_recentes,
        'depenses':     depenses_recentes,
        'derniere_sync': timezone.now().strftime('%d/%m/%Y %H:%M'),
    })