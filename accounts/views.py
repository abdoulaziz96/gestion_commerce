from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# 1. Vue de connexion
def login_view(request):
    if request.user.is_authenticated:
        # Petite vérification sur is_admin_bc (assure-toi que c'est bien une méthode)
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

# 2. Vue de déconnexion (Celle qui manquait !)
def logout_view(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté.")
    return redirect('accounts:login')

# 3. Vue de profil (Celle qui va manquer ensuite !)
@login_required
def profil_view(request):
    return render(request, 'accounts/profil.html')