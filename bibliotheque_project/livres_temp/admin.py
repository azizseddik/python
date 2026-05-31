from django.contrib import admin
from .models import Livre


@admin.register(Livre)
class LivreAdmin(admin.ModelAdmin):
    list_display  = ['titre', 'auteur', 'categorie', 'annee_publication',
                     'quantite_disponible', 'statut']
    list_filter   = ['statut', 'categorie']
    search_fields = ['titre', 'auteur']
