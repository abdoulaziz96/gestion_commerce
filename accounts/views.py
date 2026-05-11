from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone


# ── 1. Connexion ──────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_admin_bc():
            return redirect('dashboard:admin')
        return redirect('dashboard:index')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.is_admin_bc():
                return redirect('dashboard:admin')
            return redirect('dashboard:index')
        else:
            messages.error(request, 'Identifiant ou mot de passe incorrect.')

    return render(request, 'accounts/login.html')


# ── 2. Déconnexion ────────────────────────────────────────
def logout_view(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté.")
    return redirect('accounts:login')


# ── 3. Profil ─────────────────────────────────────────────
@login_required
def profil_view(request):
    from ventes.models import Vente
    from depenses.models import Depense
    from messagerie.models import Message
    from .forms import ProfilForm, ChangerMotDePasseForm

    today      = timezone.now().date()
    debut_mois = today.replace(day=1)

    # Stats selon le rôle
    if request.user.is_gestionnaire():
        nb_ventes   = Vente.objects.filter(
            gestionnaire=request.user, annulee=False
        ).count()
        ca_total    = Vente.objects.filter(
            gestionnaire=request.user, annulee=False
        ).aggregate(t=Sum('montant_total'))['t'] or 0
        ca_mois     = Vente.objects.filter(
            gestionnaire=request.user,
            date_vente__date__gte=debut_mois,
            annulee=False
        ).aggregate(t=Sum('montant_total'))['t'] or 0
        nb_depenses = Depense.objects.filter(
            gestionnaire=request.user
        ).count()
    else:  # ADMIN — voit tout
        nb_ventes   = Vente.objects.filter(annulee=False).count()
        ca_total    = Vente.objects.filter(
            annulee=False
        ).aggregate(t=Sum('montant_total'))['t'] or 0
        ca_mois     = Vente.objects.filter(
            date_vente__date__gte=debut_mois, annulee=False
        ).aggregate(t=Sum('montant_total'))['t'] or 0
        nb_depenses = Depense.objects.all().count()

    messages_non_lus = Message.objects.filter(
        destinataire=request.user, lu=False
    ).count()

    # Formulaires
    profil_form   = ProfilForm(instance=request.user)
    password_form = ChangerMotDePasseForm(request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'profil':
            profil_form = ProfilForm(
                request.POST,
                request.FILES,
                instance=request.user
            )
            if profil_form.is_valid():
                profil_form.save()
                messages.success(request, 'Profil mis à jour avec succès.')
                return redirect('accounts:profil')
            else:
                messages.error(request, 'Erreur dans le formulaire.')

        elif action == 'password':
            password_form = ChangerMotDePasseForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Mot de passe changé avec succès.')
                return redirect('accounts:profil')
            else:
                messages.error(request, 'Erreur — vérifiez les champs.')

    return render(request, 'accounts/profil.html', {
        'profil_form':      profil_form,
        'password_form':    password_form,
        'nb_ventes':        nb_ventes,
        'ca_total':         ca_total,
        'ca_mois':          ca_mois,
        'nb_depenses':      nb_depenses,
        'messages_non_lus': messages_non_lus,
    })