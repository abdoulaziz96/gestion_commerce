from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('init/', views.chatbot_init, name='init'),
    path('query/', views.chatbot_query, name='query'),
]