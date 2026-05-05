from django.urls import path
from . import views

app_name = 'depenses'

urlpatterns = [
    path('', views.depense_liste, name='liste'),
    path('ajouter/', views.depense_ajouter, name='ajouter'),
]