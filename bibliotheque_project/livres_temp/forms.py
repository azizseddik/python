from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Button
from .models import Livre


class LivreForm(forms.ModelForm):
    class Meta:
        model  = Livre
        fields = ['titre', 'auteur', 'categorie',
                  'annee_publication', 'quantite_disponible', 'statut']
        widgets = {
            'titre':  forms.TextInput(attrs={'placeholder': 'Titre du livre'}),
            'auteur': forms.TextInput(attrs={'placeholder': "Nom de l'auteur"}),
            'annee_publication':   forms.NumberInput(attrs={'placeholder': 'Ex: 1984'}),
            'quantite_disponible': forms.NumberInput(attrs={'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('titre',  css_class='col-md-8'),
                Column('auteur', css_class='col-md-4'),
            ),
            Row(
                Column('categorie',         css_class='col-md-4'),
                Column('annee_publication', css_class='col-md-4'),
                Column('statut',            css_class='col-md-4'),
            ),
            Row(
                Column('quantite_disponible', css_class='col-md-3'),
            ),
        )
