from django.urls import path
from . import views

urlpatterns = [
    path('',                          views.livre_list,   name='livre_list'),
    path('livres/ajouter/',           views.livre_create, name='livre_create'),
    path('livres/<int:pk>/modifier/', views.livre_update, name='livre_update'),
    path('livres/<int:pk>/supprimer/',views.livre_delete, name='livre_delete'),
    path('chatbot/',                  views.chatbot_page, name='chatbot'),
    path('chatbot/api/',              views.chatbot_api,  name='chatbot_api'),
    path('chatbot/clear/',            views.chatbot_clear,name='chatbot_clear'),
]
