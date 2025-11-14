from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError


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
    
    def get_proces_verbal(self):
        """Retourne le procès-verbal de ce bureau s'il existe"""
        return getattr(self, 'proces_verbal', None)
    
    def is_saisie_complete(self):
        """Vérifie si la saisie est complète pour ce bureau"""
        return hasattr(self, 'proces_verbal') and self.proces_verbal is not None


class User(AbstractUser):
    """Modèle utilisateur personnalisé"""
    ROLE_CHOICES = [
        ('candidat', 'Candidat'),
        ('representant', 'Représentant'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    parti_politique = models.CharField(max_length=100, blank=True, null=True, help_text="Parti politique (pour les candidats)")
    numero_candidat = models.IntegerField(
        blank=True, 
        null=True, 
        help_text="Numéro du candidat sur le bulletin de vote"
    )
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
        ordering = ['numero_candidat', 'first_name']
    
    def __str__(self):
        if self.role == 'candidat':
            parti = f" ({self.parti_politique})" if self.parti_politique else ""
            numero = f" N°{self.numero_candidat}" if self.numero_candidat else ""
            return f"{self.get_full_name()}{numero}{parti}"
        elif self.role == 'representant':
            bureau = f" - {self.bureau_vote}" if self.bureau_vote else " - Non affecté"
            return f"{self.get_full_name()} (Représentant){bureau}"
        return self.username
    
    def save(self, *args, **kwargs):
        # Validation: seuls les représentants peuvent avoir un bureau de vote
        if self.role != 'representant' and self.bureau_vote:
            self.bureau_vote = None
        super().save(*args, **kwargs)


class ProcesVerbal(models.Model):
    """Procès-verbal d'un bureau de vote - Données globales du bureau"""
    bureau_vote = models.OneToOneField(
        BureauVote, 
        on_delete=models.CASCADE, 
        related_name='proces_verbal'
    )
    representant = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='proces_verbaux_saisis',
        limit_choices_to={'role': 'representant'}
    )
    
    # Données du PV
    nombre_votants = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Nombre total de votants effectifs"
    )
    bulletins_nuls = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Nombre de bulletins nuls"
    )
    bulletins_blancs = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Nombre de bulletins blancs"
    )
    suffrages_exprimes = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Nombre de suffrages exprimés (calculé automatiquement)"
    )
    
    # Photo du PV officiel
    photo_pv = models.ImageField(
        upload_to='pv_photos/%Y/%m/%d/',
        help_text="Photo du procès-verbal officiel"
    )
    
    # Métadonnées
    date_saisie = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    verifie = models.BooleanField(default=False, help_text="PV vérifié par l'administrateur")
    observations = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Procès-verbal"
        verbose_name_plural = "Procès-verbaux"
        ordering = ['-date_saisie']
    
    def __str__(self):
        return f"PV - {self.bureau_vote}"
    
    # -----------------------------
    #        CLEAN() FIXÉ
    # -----------------------------
    def clean(self):
        """Validation des données du PV"""
        errors = {}
        
        # Normalisation anti-None
        nombre_votants = self.nombre_votants or 0
        bulletins_nuls = self.bulletins_nuls or 0
        bulletins_blancs = self.bulletins_blancs or 0
        
        # Vérifier que le nombre de votants ne dépasse pas les inscrits
        if hasattr(self, 'bureau_vote') and self.bureau_vote:
            if nombre_votants > self.bureau_vote.nombre_inscrits:
                errors['nombre_votants'] = (
                    f"Le nombre de votants ({nombre_votants}) "
                    f"ne peut pas dépasser le nombre d'inscrits ({self.bureau_vote.nombre_inscrits})"
                )
        
        # Calculer les suffrages exprimés
        calculated_exprimes = nombre_votants - bulletins_nuls - bulletins_blancs
        
        # Vérifier la cohérence
        if calculated_exprimes < 0:
            errors['bulletins_nuls'] = (
                "La somme des bulletins nuls et blancs ne peut pas dépasser le nombre de votants"
            )
        
        # Vérifier que la somme des voix correspond aux suffrages exprimés
        if self.pk:
            total_voix = self.resultats.aggregate(models.Sum('nombre_voix'))['nombre_voix__sum'] or 0
            if total_voix != calculated_exprimes:
                errors['__all__'] = (
                    f"La somme des voix des candidats ({total_voix}) "
                    f"doit être égale aux suffrages exprimés ({calculated_exprimes})"
                )
        
        if errors:
            raise ValidationError(errors)
        
        # Mise à jour automatique
        self.suffrages_exprimes = calculated_exprimes
    
    # -----------------------------
    #        SAVE() FIXÉ
    # -----------------------------
    def save(self, *args, **kwargs):
        n = self.nombre_votants or 0
        bn = self.bulletins_nuls or 0
        bb = self.bulletins_blancs or 0
        self.suffrages_exprimes = n - bn - bb
        super().save(*args, **kwargs)
    
    def get_taux_participation(self):
        """Calcule le taux de participation"""
        if self.bureau_vote.nombre_inscrits == 0:
            return 0
        return round((self.nombre_votants / self.bureau_vote.nombre_inscrits) * 100, 2)
    
    def get_taux_bulletins_nuls(self):
        """Calcule le taux de bulletins nuls"""
        if self.nombre_votants == 0:
            return 0
        return round((self.bulletins_nuls / self.nombre_votants) * 100, 2)


class ResultatCandidat(models.Model):
    """Résultats d'un candidat dans un bureau de vote"""
    proces_verbal = models.ForeignKey(
        ProcesVerbal,
        on_delete=models.CASCADE,
        related_name='resultats'
    )
    candidat = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='resultats_obtenus',
        limit_choices_to={'role': 'candidat'}
    )
    nombre_voix = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Nombre de voix obtenues par ce candidat"
    )
    
    class Meta:
        verbose_name = "Résultat candidat"
        verbose_name_plural = "Résultats candidats"
        ordering = ['-nombre_voix']
        unique_together = ['proces_verbal', 'candidat']
    
    def __str__(self):
        return f"{self.candidat.get_full_name()} - {self.nombre_voix} voix"
    
    def get_pourcentage(self):
        """Calcule le pourcentage de voix par rapport aux suffrages exprimés"""
        if self.proces_verbal.suffrages_exprimes == 0:
            return 0
        return round((self.nombre_voix / self.proces_verbal.suffrages_exprimes) * 100, 2)
