from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('query/', views.chatbot_query, name='query'),
]