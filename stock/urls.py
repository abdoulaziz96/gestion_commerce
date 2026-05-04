from django.urls import path
from django.shortcuts import render
app_name = 'stock'
urlpatterns = [
    path('', lambda r: render(r, 'coming_soon.html', {'module': 'Stock'}), name='liste'),
]