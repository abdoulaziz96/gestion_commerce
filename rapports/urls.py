from django.urls import path
from . import views

app_name = 'rapports'

urlpatterns = [
    path('', views.rapport_journalier, name='index'),
    path('journalier/', views.rapport_journalier, name='journalier'),
    path('mensuel/', views.rapport_mensuel, name='mensuel'),
    path('exporter/journalier/', views.exporter_pdf_journalier, name='export_pdf_journalier'),
]