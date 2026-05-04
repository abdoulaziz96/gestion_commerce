from django.urls import path
from django.shortcuts import render
app_name = 'rapports'
urlpatterns = [
    path('', lambda r: render(r, 'coming_soon.html', {'module': 'Rapports'}), name='index'),
]