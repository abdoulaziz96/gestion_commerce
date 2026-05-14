from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Produit, Categorie
from .forms import ProduitForm, CategorieForm


@login_required
def produit_liste(request):
    onglet    = request.GET.get('onglet', 'produits')
    query     = request.GET.get('q', '')
    categorie = request.GET.get('categorie', '')
    alerte    = request.GET.get('alerte', '')

    produits   = Produit.objects.filter(actif=True).select_related('categorie')
    categories = Categorie.objects.all()

    # Filtres onglet produits
    if query:
        produits = produits.filter(
            Q(nom__icontains=query) | Q(description__icontains=query)
        )
    if categorie:
        produits = produits.filter(categorie__id=categorie)
    if alerte:
        produits = [p for p in produits if p.en_alerte]

    # ── Onglet catégories : ajout ──
    cat_form = CategorieForm()
    if request.method == 'POST' and 'ajouter_categorie' in request.POST:
        cat_form = CategorieForm(request.POST)
        if cat_form.is_valid():
            cat_form.save()
            messages.success(request, 'Catégorie ajoutée avec succès.')
            return redirect('/produits/?onglet=categories')
        else:
            onglet = 'categories'  # rester sur l'onglet si erreur

    # ── Onglet catégories : suppression ──
    if request.method == 'POST' and 'supprimer_categorie' in request.POST:
        cat_id = request.POST.get('cat_id')
        cat    = get_object_or_404(Categorie, pk=cat_id)
        if cat.produits.exists():
            messages.error(
                request,
                f'Impossible : "{cat.nom}" contient des produits.'
            )
        else:
            cat.delete()
            messages.success(request, f'Catégorie "{cat.nom}" supprimée.')
        return redirect('/produits/?onglet=categories')

    return render(request, 'produits/liste.html', {
        'produits':   produits,
        'categories': categories,
        'cat_form':   cat_form,
        'query':      query,
        'onglet':     onglet,
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
        if produit.ventes.exists():
            messages.error(
                request,
                'Impossible de supprimer : ce produit a des ventes associées.'
            )
            return redirect('produits:liste')
        produit.actif = False
        produit.save()
        messages.success(request, 'Produit supprimé.')
        return redirect('produits:liste')

    return render(
        request,
        'produits/confirmer_suppression.html',
        {'produit': produit}
    )


# Cette vue reste pour compatibilité URL mais redirige vers l'onglet
@login_required
def categorie_liste(request):
    return redirect('/produits/?onglet=categories')