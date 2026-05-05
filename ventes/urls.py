from django.urls import path
from . import views

app_name = 'ventes'

urlpatterns = [
    path('', views.vente_liste, name='liste'),
    path('enregistrer/', views.vente_enregistrer, name='enregistrer'),
    path('<int:pk>/annuler/', views.vente_annuler, name='annuler'),
]