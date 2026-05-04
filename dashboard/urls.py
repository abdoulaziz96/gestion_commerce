from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('dashboard/', views.dashboard_gestionnaire, name='index'),
    path('admin-dashboard/', views.dashboard_admin, name='admin'),
]