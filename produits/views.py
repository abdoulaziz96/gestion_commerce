from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Produit, Categorie
from .forms import ProduitForm, CategorieForm


@login_required
def produit_liste(request):
    query      = request.GET.get('q', '')
    categorie  = request.GET.get('categorie', '')
    alerte     = request.GET.get('alerte', '')

    produits = Produit.objects.filter(actif=True).select_related('categorie')

    if query:
        produits = produits.filter(
            Q(nom__icontains=query) | Q(description__icontains=query)
        )
    if categorie:
        produits = produits.filter(categorie__id=categorie)
    if alerte:
        produits = [p for p in produits if p.en_alerte]

    categories = Categorie.objects.all()

    return render(request, 'produits/liste.html', {
        'produits':   produits,
        'categories': categories,
        'query':      query,
    })


@login_required
def produit_ajouter(request):
    form = ProduitForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Produit ajouté avec succès.')
        return redirect('produits:liste')

    return render(request, 'produits/form.html', {
        'form':  form,
        'titre': 'Ajouter un produit',
    })


@login_required
def produit_modifier(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    form    = ProduitForm(
        request.POST  or None,
        request.FILES or None,
        instance=produit
    )
    if form.is_valid():
        form.save()
        messages.success(request, 'Produit modifié avec succès.')
        return redirect('produits:liste')

    return render(request, 'produits/form.html', {
        'form':    form,
        'titre':   'Modifier le produit',
        'produit': produit,
    })


@login_required
def produit_supprimer(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        # Bloqué si des ventes existent (règle métier cahier des charges)
        if produit.ventes.exists():
            messages.error(request, 'Impossible de supprimer : ce produit a des ventes associées.')
            return redirect('produits:liste')
        produit.actif = False  # Soft delete
        produit.save()
        messages.success(request, 'Produit supprimé.')
        return redirect('produits:liste')

    return render(request, 'produits/confirmer_suppression.html', {'produit': produit})


@login_required
def categorie_liste(request):
    form       = CategorieForm(request.POST or None)
    categories = Categorie.objects.all()

    if form.is_valid():
        form.save()
        messages.success(request, 'Catégorie ajoutée.')
        return redirect('produits:categories')

    return render(request, 'produits/categories.html', {
        'form':       form,
        'categories': categories,
    })