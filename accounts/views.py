from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Utilisateur


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if user.is_admin_bc():
                return redirect('dashboard:admin')
            return redirect('dashboard:index')
        else:
            messages.error(request, 'Identifiant ou mot de passe incorrect.')

    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def profil_view(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name  = request.POST.get('last_name', '')
        user.email      = request.POST.get('email', '')
        user.save()
        messages.success(request, 'Profil mis à jour avec succès.')
        return redirect('accounts:profil')

    return render(request, 'accounts/profil.html')