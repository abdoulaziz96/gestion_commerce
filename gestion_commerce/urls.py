from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render, redirect  


from django.contrib import admin
admin.site.site_header = "IBRAFRIK Decor — Administration"
admin.site.site_title  = "IBRAFRIK Decor"
admin.site.index_title = "Tableau de bord administrateur"
urlpatterns = [
    path('', lambda r: redirect('dashboard:index'), name='home'),
    path('admin/', admin.site.urls),
     path('accounts/', include('allauth.urls')), 
    path('', include('accounts.urls')),
    path('', include('dashboard.urls')),
    path('produits/', include('produits.urls')),
    path('ventes/', include('ventes.urls')),
    path('depenses/', include('depenses.urls')),
    path('stock/', include('stock.urls')),
    path('rapports/', include('rapports.urls')),
    path('messagerie/', include('messagerie.urls')),
    path('sync/', include('sync.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)