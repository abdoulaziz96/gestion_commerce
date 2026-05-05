from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Vente
from .forms import VenteForm


@login_required
def vente_liste(request):
    ventes = Vente.objects.filter(
        gestionnaire=request.user
    ).select_related('produit').order_by('-date_vente')

    # Filtres
    date_debut = request.GET.get('date_debut')
    date_fin   = request.GET.get('date_fin')
    produit_q  = request.GET.get('produit', '')

    if date_debut:
        ventes = ventes.filter(date_vente__date__gte=date_debut)
    if date_fin:
        ventes = ventes.filter(date_vente__date__lte=date_fin)
    if produit_q:
        ventes = ventes.filter(produit__nom__icontains=produit_q)

    total = sum(v.montant_total for v in ventes if not v.annulee)

    return render(request, 'ventes/liste.html', {
        'ventes': ventes,
        'total':  total,
    })


@login_required
@transaction.atomic
def vente_enregistrer(request):
    form = VenteForm(request.POST or None)

    if form.is_valid():
        vente = form.save(commit=False)
        vente.gestionnaire = request.user

        # Déduire du stock
        produit = vente.produit
        produit.quantite_stock -= vente.quantite
        produit.save()

        vente.save()
        messages.success(request, f'Vente enregistrée — {vente.montant_total} FCFA')
        return redirect('ventes:liste')

    return render(request, 'ventes/form.html', {'form': form})


@login_required
@transaction.atomic
def vente_annuler(request, pk):
    vente = get_object_or_404(Vente, pk=pk, gestionnaire=request.user)

    if vente.annulee:
        messages.warning(request, 'Cette vente est déjà annulée.')
        return redirect('ventes:liste')

    if request.method == 'POST':
        # Remettre en stock
        vente.produit.quantite_stock += vente.quantite
        vente.produit.save()
        vente.annulee = True
        vente.save()
        messages.success(request, 'Vente annulée — stock remis à jour.')
        return redirect('ventes:liste')

    return render(request, 'ventes/confirmer_annulation.html', {'vente': vente})