from django.urls import path
from django.shortcuts import render
app_name = 'messagerie'
urlpatterns = [
    path('', lambda r: render(r, 'coming_soon.html', {'module': 'Messagerie'}), name='inbox'),
]