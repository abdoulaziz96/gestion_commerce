from django.urls import path
from . import views

app_name = 'stock'

urlpatterns = [
    path('', views.stock_liste, name='liste'),
    path('entree/', views.entree_stock, name='entree'),
    path('sortie/', views.sortie_stock, name='sortie'),
    path('historique/', views.mouvements_liste, name='historique'),
    path('inventaire/', views.inventaire, name='inventaire'),
]