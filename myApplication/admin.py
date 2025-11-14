from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.db.models import Sum
from .models import (
    Departement, SousPrefecture, CentreVote, 
    BureauVote, User, ProcesVerbal, ResultatCandidat
)


@admin.register(Departement)
class DepartementAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code', 'nombre_sous_prefectures']
    search_fields = ['nom', 'code']
    
    def nombre_sous_prefectures(self, obj):
        return obj.sous_prefectures.count()
    nombre_sous_prefectures.short_description = "Sous-préfectures"


@admin.register(SousPrefecture)
class SousPrefectureAdmin(admin.ModelAdmin):
    list_display = ['nom', 'departement', 'nombre_centres']
    list_filter = ['departement']
    search_fields = ['nom', 'departement__nom']
    
    def nombre_centres(self, obj):
        return obj.centres_vote.count()
    nombre_centres.short_description = "Centres de vote"


@admin.register(CentreVote)
class CentreVoteAdmin(admin.ModelAdmin):
    list_display = ['nom', 'sous_prefecture', 'departement', 'nombre_bureaux']
    list_filter = ['sous_prefecture__departement', 'sous_prefecture']
    search_fields = ['nom', 'sous_prefecture__nom']
    
    def departement(self, obj):
        return obj.sous_prefecture.departement.nom
    departement.short_description = "Département"
    
    def nombre_bureaux(self, obj):
        return obj.bureaux.count()
    nombre_bureaux.short_description = "Bureaux"


@admin.register(BureauVote)
class BureauVoteAdmin(admin.ModelAdmin):
    list_display = ['numero', 'centre_vote', 'sous_prefecture', 'nombre_inscrits', 'pv_saisi']
    list_filter = ['centre_vote__sous_prefecture__departement', 'centre_vote__sous_prefecture']
    search_fields = ['numero', 'centre_vote__nom']
    
    def sous_prefecture(self, obj):
        return obj.centre_vote.sous_prefecture.nom
    sous_prefecture.short_description = "Sous-préfecture"
    
    def pv_saisi(self, obj):
        pv = obj.get_proces_verbal()
        if pv:
            return format_html('<span style="color: green;">✓ PV saisi</span>')
        return format_html('<span style="color: red;">✗ Aucun PV</span>')
    pv_saisi.short_description = "Statut"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'numero_candidat', 'parti_politique', 'bureau_affecte', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'telephone', 'parti_politique']
    ordering = ['numero_candidat', 'first_name']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations électorales', {
            'fields': ('role', 'numero_candidat', 'parti_politique', 'telephone', 'bureau_vote')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informations électorales', {
            'fields': ('role', 'numero_candidat', 'parti_politique', 'telephone', 'bureau_vote', 'first_name', 'last_name', 'email')
        }),
    )
    
    def bureau_affecte(self, obj):
        if obj.role == 'representant' and obj.bureau_vote:
            return format_html('<span style="color: green;">✓ {}</span>', obj.bureau_vote)
        elif obj.role == 'representant':
            return format_html('<span style="color: orange;">⚠ Non affecté</span>')
        return '-'
    bureau_affecte.short_description = "Bureau affecté"


class ResultatCandidatInline(admin.TabularInline):
    model = ResultatCandidat
    extra = 0
    fields = ['candidat', 'nombre_voix', 'pourcentage']
    readonly_fields = ['pourcentage']
    
    def pourcentage(self, obj):
        if obj.pk:
            return f"{obj.get_pourcentage()}%"
        return "-"
    pourcentage.short_description = "% des voix"


@admin.register(ProcesVerbal)
class ProcesVerbalAdmin(admin.ModelAdmin):
    list_display = [
        'bureau_vote', 'nombre_votants', 'bulletins_nuls', 'bulletins_blancs',
        'suffrages_exprimes', 'representant', 'verifie', 'apercu_photo', 'date_saisie'
    ]
    list_filter = [
        'verifie', 'date_saisie',
        'bureau_vote__centre_vote__sous_prefecture__departement',
        'bureau_vote__centre_vote__sous_prefecture'
    ]
    search_fields = [
        'bureau_vote__numero', 'bureau_vote__centre_vote__nom',
        'representant__first_name', 'representant__last_name'
    ]
    readonly_fields = ['date_saisie', 'date_modification', 'apercu_photo_large', 'taux_participation', 'taux_nuls']
    inlines = [ResultatCandidatInline]
    
    fieldsets = (
        ('Bureau de vote', {
            'fields': ('bureau_vote', 'representant')
        }),
        ('Données du PV', {
            'fields': ('nombre_votants', 'bulletins_nuls', 'bulletins_blancs', 'suffrages_exprimes')
        }),
        ('Statistiques', {
            'fields': ('taux_participation', 'taux_nuls'),
            'classes': ('collapse',)
        }),
        ('Justificatif', {
            'fields': ('photo_pv', 'apercu_photo_large')
        }),
        ('Validation', {
            'fields': ('verifie', 'observations')
        }),
        ('Métadonnées', {
            'fields': ('date_saisie', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def apercu_photo(self, obj):
        if obj.photo_pv:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />',
                obj.photo_pv.url
            )
        return '-'
    apercu_photo.short_description = "PV"
    
    def apercu_photo_large(self, obj):
        if obj.photo_pv:
            return format_html(
                '<img src="{}" style="max-width: 600px; max-height: 600px; border-radius: 8px;" />',
                obj.photo_pv.url
            )
        return 'Aucune photo'
    apercu_photo_large.short_description = "Aperçu du procès-verbal"
    
    def taux_participation(self, obj):
        return f"{obj.get_taux_participation()}%"
    taux_participation.short_description = "Taux de participation"
    
    def taux_nuls(self, obj):
        return f"{obj.get_taux_bulletins_nuls()}%"
    taux_nuls.short_description = "Taux de bulletins nuls"


@admin.register(ResultatCandidat)
class ResultatCandidatAdmin(admin.ModelAdmin):
    list_display = ['candidat', 'bureau', 'nombre_voix', 'pourcentage', 'verifie', 'date_saisie']
    list_filter = [
        'proces_verbal__verifie',
        'candidat',
        'proces_verbal__date_saisie',
        'proces_verbal__bureau_vote__centre_vote__sous_prefecture__departement'
    ]
    search_fields = [
        'candidat__first_name', 'candidat__last_name',
        'proces_verbal__bureau_vote__numero',
        'proces_verbal__bureau_vote__centre_vote__nom'
    ]
    readonly_fields = ['pourcentage', 'date_saisie']
    
    def bureau(self, obj):
        return obj.proces_verbal.bureau_vote
    bureau.short_description = "Bureau de vote"
    
    def pourcentage(self, obj):
        return f"{obj.get_pourcentage()}%"
    pourcentage.short_description = "% des suffrages exprimés"
    
    def verifie(self, obj):
        if obj.proces_verbal.verifie:
            return format_html('<span style="color: green;">✓ Vérifié</span>')
        return format_html('<span style="color: orange;">⏳ En attente</span>')
    verifie.short_description = "Statut"
    
    def date_saisie(self, obj):
        return obj.proces_verbal.date_saisie
    date_saisie.short_description = "Date de saisie"


# Personnalisation du site admin
admin.site.site_header = "Administration Électorale"
admin.site.site_title = "Gestion des Résultats"
admin.site.index_title = "Tableau de bord"