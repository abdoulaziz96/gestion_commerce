from django.urls import path
from . import views

app_name = 'messagerie'

urlpatterns = [
    path('', views.inbox, name='inbox'),  # URL: /messagerie/
    path('envoyer/', views.envoyer, name='envoyer'),  # URL: /messagerie/envoyer/
    path('envoyes/', views.sent, name='sent'),  # URL: /messagerie/envoyes/
    path('detail/<int:pk>/', views.message_detail, name='detail'), # URL: /messagerie/detail/1/
]