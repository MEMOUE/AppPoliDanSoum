from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


class Departement(models.Model):
    """Modèle pour les départements"""
    nom = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    
    class Meta:
        verbose_name = "Département"
        verbose_name_plural = "Départements"
        ordering = ['nom']
    
    def __str__(self):
        return self.nom


class SousPrefecture(models.Model):
    """Modèle pour les sous-préfectures"""
    nom = models.CharField(max_length=100)
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, related_name='sous_prefectures')
    
    class Meta:
        verbose_name = "Sous-préfecture"
        verbose_name_plural = "Sous-préfectures"
        ordering = ['nom']
        unique_together = ['nom', 'departement']
    
    def __str__(self):
        return f"{self.nom} ({self.departement.nom})"


class CentreVote(models.Model):
    """Modèle pour les centres de vote (écoles, lieux publics, etc.)"""
    nom = models.CharField(max_length=200)
    sous_prefecture = models.ForeignKey(SousPrefecture, on_delete=models.CASCADE, related_name='centres_vote')
    adresse = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Centre de vote"
        verbose_name_plural = "Centres de vote"
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} - {self.sous_prefecture.nom}"


class BureauVote(models.Model):
    """Modèle pour les bureaux de vote"""
    numero = models.CharField(max_length=10)
    centre_vote = models.ForeignKey(CentreVote, on_delete=models.CASCADE, related_name='bureaux')
    nombre_inscrits = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    class Meta:
        verbose_name = "Bureau de vote"
        verbose_name_plural = "Bureaux de vote"
        ordering = ['centre_vote', 'numero']
        unique_together = ['numero', 'centre_vote']
    
    def __str__(self):
        return f"Bureau {self.numero} - {self.centre_vote.nom}"


class User(AbstractUser):
    """Modèle utilisateur personnalisé"""
    ROLE_CHOICES = [
        ('candidat', 'Candidat'),
        ('representant', 'Représentant'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    bureau_vote = models.ForeignKey(
        BureauVote, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='representants',
        help_text="Bureau de vote affecté (pour les représentants uniquement)"
    )
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
    
    def __str__(self):
        if self.role == 'candidat':
            return f"{self.get_full_name()} (Candidat)"
        elif self.role == 'representant':
            bureau = f" - {self.bureau_vote}" if self.bureau_vote else " - Non affecté"
            return f"{self.get_full_name()} (Représentant){bureau}"
        return self.username
    
    def save(self, *args, **kwargs):
        # Validation: seuls les représentants peuvent avoir un bureau de vote
        if self.role != 'representant' and self.bureau_vote:
            self.bureau_vote = None
        super().save(*args, **kwargs)


class Resultat(models.Model):
    """Modèle pour stocker les résultats par bureau de vote"""
    candidat = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='resultats',
        limit_choices_to={'role': 'candidat'}
    )
    bureau_vote = models.ForeignKey(BureauVote, on_delete=models.CASCADE, related_name='resultats')
    representant = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='resultats_saisis',
        limit_choices_to={'role': 'representant'}
    )
    
    nombre_voix = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Nombre de voix obtenues"
    )
    photo_pv = models.ImageField(
        upload_to='pv_photos/%Y/%m/%d/',
        help_text="Photo du procès-verbal"
    )
    
    date_saisie = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    verifie = models.BooleanField(default=False, help_text="Résultat vérifié par l'administrateur")
    
    observations = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Résultat"
        verbose_name_plural = "Résultats"
        ordering = ['-date_saisie']
        unique_together = ['candidat', 'bureau_vote']
    
    def __str__(self):
        return f"{self.candidat.get_full_name()} - {self.bureau_vote} - {self.nombre_voix} voix"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        # Vérifier que le nombre de voix ne dépasse pas le nombre d'inscrits
        if self.nombre_voix > self.bureau_vote.nombre_inscrits:
            raise ValidationError(
                f"Le nombre de voix ({self.nombre_voix}) ne peut pas dépasser "
                f"le nombre d'inscrits ({self.bureau_vote.nombre_inscrits})"
            )