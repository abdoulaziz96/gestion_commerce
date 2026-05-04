from django.urls import path
from django.shortcuts import render
app_name = 'depenses'
urlpatterns = [
    path('', lambda r: render(r, 'coming_soon.html', {'module': 'Dépenses'}), name='liste'),
]