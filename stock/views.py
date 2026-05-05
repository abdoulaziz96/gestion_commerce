from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import MouvementStock
from .forms import EntreeStockForm, SortieStockForm, InventaireForm
from produits.models import Produit


@login_required
def stock_liste(request):
    produits = Produit.objects.filter(actif=True).select_related('categorie')
    alertes  = [p for p in produits if p.en_alerte]

    return render(request, 'stock/liste.html', {
        'produits': produits,
        'alertes':  alertes,
    })


@login_required
@transaction.atomic
def entree_stock(request):
    form = EntreeStockForm(request.POST or None)

    if form.is_valid():
        produit  = form.cleaned_data['produit']
        quantite = form.cleaned_data['quantite']
        motif    = form.cleaned_data['motif']

        # Mettre à jour le stock
        produit.quantite_stock += quantite
        produit.save()

        # Enregistrer le mouvement
        MouvementStock.objects.create(
            produit=produit,
            type_mouvement=MouvementStock.ENTREE,
            quantite=quantite,
            motif=motif,
            gestionnaire=request.user,
        )

        messages.success(request, f'+{quantite} unité(s) ajoutée(s) pour {produit.nom}.')
        return redirect('stock:liste')

    return render(request, 'stock/entree.html', {'form': form})


@login_required
@transaction.atomic
def sortie_stock(request):
    form = SortieStockForm(request.POST or None)

    if form.is_valid():
        produit  = form.cleaned_data['produit']
        quantite = form.cleaned_data['quantite']
        motif    = form.cleaned_data['motif']

        if quantite > produit.quantite_stock:
            messages.error(request, f'Stock insuffisant. Disponible : {produit.quantite_stock}')
            return render(request, 'stock/sortie.html', {'form': form})

        produit.quantite_stock -= quantite
        produit.save()

        MouvementStock.objects.create(
            produit=produit,
            type_mouvement=MouvementStock.SORTIE,
            quantite=quantite,
            motif=motif,
            gestionnaire=request.user,
        )

        messages.success(request, f'-{quantite} unité(s) retirée(s) pour {produit.nom}.')
        return redirect('stock:liste')

    return render(request, 'stock/sortie.html', {'form': form})


@login_required
def mouvements_liste(request):
    mouvements = MouvementStock.objects.all().select_related(
        'produit', 'gestionnaire'
    ).order_by('-date_mouvement')

    produit_q = request.GET.get('produit', '')
    type_q    = request.GET.get('type', '')

    if produit_q:
        mouvements = mouvements.filter(produit__nom__icontains=produit_q)
    if type_q:
        mouvements = mouvements.filter(type_mouvement=type_q)

    return render(request, 'stock/historique.html', {
        'mouvements': mouvements,
        'types':      MouvementStock.TYPE_CHOICES,
    })


@login_required
@transaction.atomic
def inventaire(request):
    produits = Produit.objects.filter(actif=True)
    form     = InventaireForm(request.POST or None, produits=produits)

    if form.is_valid():
        for produit in produits:
            champ    = f'stock_{produit.pk}'
            nouveau  = form.cleaned_data.get(champ)
            if nouveau is not None and nouveau != produit.quantite_stock:
                ecart = nouveau - produit.quantite_stock
                MouvementStock.objects.create(
                    produit=produit,
                    type_mouvement=MouvementStock.AJUSTEMENT,
                    quantite=abs(ecart),
                    motif=f'Inventaire — ajustement {"+" if ecart > 0 else ""}{ecart}',
                    gestionnaire=request.user,
                )
                produit.quantite_stock = nouveau
                produit.save()

        messages.success(request, 'Inventaire enregistré avec succès.')
        return redirect('stock:liste')

    return render(request, 'stock/inventaire.html', {
        'form':     form,
        'produits': produits,
    })