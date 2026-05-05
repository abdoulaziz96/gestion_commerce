from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Count
from accounts.decorators import role_required
from ventes.models import Vente
from depenses.models import Depense
from produits.models import Produit
from stock.models import MouvementStock
import json


@login_required
def dashboard_gestionnaire(request):
    aujourd_hui = timezone.now().date()
    debut_mois  = aujourd_hui.replace(day=1)

    # Ventes du jour
    ventes_jour = Vente.objects.filter(
        gestionnaire=request.user,
        date_vente__date=aujourd_hui,
        annulee=False
    )
    ca_jour = ventes_jour.aggregate(t=Sum('montant_total'))['t'] or 0
    nb_ventes_jour = ventes_jour.count()

    # Ventes du mois
    ventes_mois = Vente.objects.filter(
        gestionnaire=request.user,
        date_vente__date__gte=debut_mois,
        annulee=False
    )
    ca_mois = ventes_mois.aggregate(t=Sum('montant_total'))['t'] or 0

    # Dépenses du mois
    depenses_mois = Depense.objects.filter(
        gestionnaire=request.user,
        date_depense__gte=debut_mois
    ).aggregate(t=Sum('montant'))['t'] or 0

    # Bénéfice net
    benefice = ca_mois - depenses_mois

    # Produits en alerte
    produits_alerte = [p for p in Produit.objects.filter(actif=True) if p.en_alerte]

    # Top 5 produits vendus ce mois
    top_produits = Vente.objects.filter(
        gestionnaire=request.user,
        date_vente__date__gte=debut_mois,
        annulee=False
    ).values('produit__nom').annotate(
        total_qte=Sum('quantite'),
        total_ca=Sum('montant_total')
    ).order_by('-total_qte')[:5]

    # Graphique : ventes 7 derniers jours
    labels, data_ca = [], []
    for i in range(6, -1, -1):
        jour = aujourd_hui - timezone.timedelta(days=i)
        ca   = Vente.objects.filter(
            gestionnaire=request.user,
            date_vente__date=jour,
            annulee=False
        ).aggregate(t=Sum('montant_total'))['t'] or 0
        labels.append(jour.strftime('%d/%m'))
        data_ca.append(float(ca))

    return render(request, 'dashboard/gestionnaire.html', {
        'ca_jour':         ca_jour,
        'nb_ventes_jour':  nb_ventes_jour,
        'ca_mois':         ca_mois,
        'depenses_mois':   depenses_mois,
        'benefice':        benefice,
        'produits_alerte': produits_alerte,
        'top_produits':    top_produits,
        'labels':          json.dumps(labels),
        'data_ca':         json.dumps(data_ca),
    })


@login_required
@role_required('ADMIN')
def dashboard_admin(request):
    aujourd_hui = timezone.now().date()
    debut_mois  = aujourd_hui.replace(day=1)
    debut_sem   = aujourd_hui - timezone.timedelta(days=aujourd_hui.weekday())

    # CA global
    ca_jour  = Vente.objects.filter(
        date_vente__date=aujourd_hui, annulee=False
    ).aggregate(t=Sum('montant_total'))['t'] or 0

    ca_semaine = Vente.objects.filter(
        date_vente__date__gte=debut_sem, annulee=False
    ).aggregate(t=Sum('montant_total'))['t'] or 0

    ca_mois = Vente.objects.filter(
        date_vente__date__gte=debut_mois, annulee=False
    ).aggregate(t=Sum('montant_total'))['t'] or 0

    depenses_mois = Depense.objects.filter(
        date_depense__gte=debut_mois
    ).aggregate(t=Sum('montant'))['t'] or 0

    benefice_net = ca_mois - depenses_mois
    nb_ventes    = Vente.objects.filter(
        date_vente__date__gte=debut_mois, annulee=False
    ).count()

    # Alertes stock
    produits_alerte = [p for p in Produit.objects.filter(actif=True) if p.en_alerte]

    # Graphique 30 jours
    labels, data_ca, data_dep = [], [], []
    for i in range(29, -1, -1):
        jour = aujourd_hui - timezone.timedelta(days=i)
        ca   = Vente.objects.filter(
            date_vente__date=jour, annulee=False
        ).aggregate(t=Sum('montant_total'))['t'] or 0
        dep  = Depense.objects.filter(
            date_depense=jour
        ).aggregate(t=Sum('montant'))['t'] or 0
        labels.append(jour.strftime('%d/%m'))
        data_ca.append(float(ca))
        data_dep.append(float(dep))

    # Messages non lus
    from messagerie.models import Message
    messages_non_lus = Message.objects.filter(
        destinataire=request.user, lu=False
    ).count()

    return render(request, 'dashboard/admin.html', {
        'ca_jour':          ca_jour,
        'ca_semaine':       ca_semaine,
        'ca_mois':          ca_mois,
        'depenses_mois':    depenses_mois,
        'benefice_net':     benefice_net,
        'nb_ventes':        nb_ventes,
        'produits_alerte':  produits_alerte,
        'labels':           json.dumps(labels),
        'data_ca':          json.dumps(data_ca),
        'data_dep':         json.dumps(data_dep),
        'messages_non_lus': messages_non_lus,
    })