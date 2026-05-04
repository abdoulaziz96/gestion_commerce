from django.urls import path
from django.shortcuts import render
app_name = 'ventes'
urlpatterns = [
    path('', lambda r: render(r, 'coming_soon.html', {'module': 'Ventes'}), name='liste'),
]