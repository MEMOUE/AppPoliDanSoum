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
















# Ajout au fichier models.py existant

class AuditLog(models.Model):
    """Journal des modifications pour traçabilité"""

    ACTION_CHOICES = [
        ('CREATE', 'Création'),
        ('UPDATE', 'Modification'),
        ('DELETE', 'Suppression'),
        ('VIEW', 'Consultation'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50)
    object_id = models.IntegerField()
    object_repr = models.CharField(max_length=200, blank=True)
    changes = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)

    class Meta:
        verbose_name = "Journal d'audit"
        verbose_name_plural = "Journaux d'audit"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['model_name', 'object_id']),
        ]

    def __str__(self):
        user_str = self.user.get_full_name() if self.user else "Système"
        return f"{user_str} - {self.get_action_display()} - {self.model_name} #{self.object_id} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"

    @classmethod
    def log_action(cls, user, action, instance, changes=None, request=None):
        """
        Méthode utilitaire pour logger une action

        Usage:
            AuditLog.log_action(
                user=request.user,
                action='UPDATE',
                instance=pv_instance,
                changes={'nombre_votants': {'old': 100, 'new': 105}},
                request=request
            )
        """
        ip_address = None
        user_agent = ""

        if request:
            # Obtenir l'IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')

            # Obtenir le User-Agent
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

        return cls.objects.create(
            user=user,
            action=action,
            model_name=instance.__class__.__name__,
            object_id=instance.pk,
            object_repr=str(instance)[:200],
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent
        )


# ========================================
# FONCTION UTILITAIRE POUR DÉTECTER LES CHANGEMENTS
# ========================================

def get_model_changes(old_instance, new_instance, fields_to_track):
    """
    Compare deux instances d'un modèle et retourne les changements

    Args:
        old_instance: Instance avant modification
        new_instance: Instance après modification
        fields_to_track: Liste des champs à surveiller

    Returns:
        dict: Dictionnaire des changements {field: {'old': value, 'new': value}}
    """
    changes = {}

    for field in fields_to_track:
        old_value = getattr(old_instance, field, None)
        new_value = getattr(new_instance, field, None)

        if old_value != new_value:
            changes[field] = {
                'old': str(old_value),
                'new': str(new_value)
            }

    return changes if changes else None


# ========================================
# EXEMPLE D'UTILISATION DANS views.py
# ========================================

"""
Dans la vue saisie_resultat, après la sauvegarde du PV :

# Déterminer l'action
action = 'UPDATE' if pv_existant else 'CREATE'

# Tracker les changements si c'est une modification
changes = None
if pv_existant:
    fields_to_track = ['nombre_votants', 'bulletins_nuls', 'bulletins_blancs', 'suffrages_exprimes']
    changes = get_model_changes(pv_existant, pv, fields_to_track)

# Logger l'action
AuditLog.log_action(
    user=request.user,
    action=action,
    instance=pv,
    changes=changes,
    request=request
)

messages.success(request, f'✅ Procès-verbal {action.lower()}é avec succès !')
"""


# ========================================
# ADMIN POUR AUDITLOG
# ========================================

"""
Dans admin.py :

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'model_name', 'object_id', 'ip_address']
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'object_repr', 'ip_address']
    readonly_fields = ['timestamp', 'user', 'action', 'model_name', 'object_id', 'object_repr', 'changes', 'ip_address', 'user_agent']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False  # Les logs ne peuvent pas être créés manuellement
    
    def has_change_permission(self, request, obj=None):
        return False  # Les logs ne peuvent pas être modifiés
    
    def has_delete_permission(self, request, obj=None):
        return False  # Les logs ne peuvent pas être supprimés
"""
