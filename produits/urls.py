from django.urls import path
from . import views

app_name = 'produits'

urlpatterns = [
    path('', views.produit_liste, name='liste'),
    path('ajouter/', views.produit_ajouter, name='ajouter'),
    path('<int:pk>/modifier/', views.produit_modifier, name='modifier'),
    path('<int:pk>/supprimer/', views.produit_supprimer, name='supprimer'),
    path('categories/', views.categorie_liste, name='categories'),
]