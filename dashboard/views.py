from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required


@login_required
def dashboard_gestionnaire(request):
    return render(request, 'dashboard/gestionnaire.html')


@login_required
def dashboard_admin(request):
    return render(request, 'dashboard/admin.html')