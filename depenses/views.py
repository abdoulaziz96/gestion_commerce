from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Depense
from .forms import DepenseForm


@login_required
def depense_liste(request):
    depenses = Depense.objects.filter(
        gestionnaire=request.user
    ).order_by('-date_depense')

    date_debut = request.GET.get('date_debut')
    date_fin   = request.GET.get('date_fin')

    if date_debut:
        depenses = depenses.filter(date_depense__gte=date_debut)
    if date_fin:
        depenses = depenses.filter(date_depense__lte=date_fin)

    total = sum(d.montant for d in depenses)

    return render(request, 'depenses/liste.html', {
        'depenses': depenses,
        'total':    total,
    })


@login_required
def depense_ajouter(request):
    form = DepenseForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        depense = form.save(commit=False)
        depense.gestionnaire = request.user
        depense.save()
        messages.success(request, 'Dépense enregistrée.')
        return redirect('depenses:liste')

    return render(request, 'depenses/form.html', {'form': form})