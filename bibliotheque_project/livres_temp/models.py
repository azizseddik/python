from django.db import models


class Livre(models.Model):
    STATUT_CHOICES = [
        ('disponible', 'Disponible'),
        ('emprunté',   'Emprunté'),
        ('réservé',    'Réservé'),
    ]
    CATEGORIE_CHOICES = [
        ('Roman',        'Roman'),
        ('Science',      'Science'),
        ('Histoire',     'Histoire'),
        ('Informatique', 'Informatique'),
        ('Philosophie',  'Philosophie'),
        ('Poésie',       'Poésie'),
        ('Biographie',   'Biographie'),
        ('Autre',        'Autre'),
    ]

    titre               = models.CharField(max_length=255)
    auteur              = models.CharField(max_length=255)
    categorie           = models.CharField(max_length=100, choices=CATEGORIE_CHOICES, blank=True)
    annee_publication   = models.IntegerField(null=True, blank=True)
    quantite_disponible = models.IntegerField(default=0)
    statut              = models.CharField(max_length=20, choices=STATUT_CHOICES, default='disponible')

    class Meta:
        verbose_name        = 'Livre'
        verbose_name_plural = 'Livres'
        ordering            = ['titre']

    def __str__(self):
        return f"{self.titre} — {self.auteur}"
