from django.urls import path
from . import views

app_name = 'sync'

urlpatterns = [
    path('statut/', views.statut_sync, name='statut'),
]