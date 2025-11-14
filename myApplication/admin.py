from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import (
    Departement, SousPrefecture, CentreVote, 
    BureauVote, User, Resultat
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
    list_display = ['numero', 'centre_vote', 'sous_prefecture', 'nombre_inscrits', 'resultats_saisis']
    list_filter = ['centre_vote__sous_prefecture__departement', 'centre_vote__sous_prefecture']
    search_fields = ['numero', 'centre_vote__nom']
    
    def sous_prefecture(self, obj):
        return obj.centre_vote.sous_prefecture.nom
    sous_prefecture.short_description = "Sous-préfecture"
    
    def resultats_saisis(self, obj):
        count = obj.resultats.count()
        if count > 0:
            return format_html('<span style="color: green;">✓ {} résultat(s)</span>', count)
        return format_html('<span style="color: red;">✗ Aucun résultat</span>')
    resultats_saisis.short_description = "Résultats"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'telephone', 'bureau_affecte', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'telephone']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations électorales', {
            'fields': ('role', 'telephone', 'bureau_vote')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informations électorales', {
            'fields': ('role', 'telephone', 'bureau_vote', 'first_name', 'last_name', 'email')
        }),
    )
    
    def bureau_affecte(self, obj):
        if obj.role == 'representant' and obj.bureau_vote:
            return format_html(
                '<span style="color: green;">✓ {}</span>', 
                obj.bureau_vote
            )
        elif obj.role == 'representant':
            return format_html('<span style="color: orange;">⚠ Non affecté</span>')
        return '-'
    bureau_affecte.short_description = "Bureau affecté"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('bureau_vote', 'bureau_vote__centre_vote', 'bureau_vote__centre_vote__sous_prefecture')


@admin.register(Resultat)
class ResultatAdmin(admin.ModelAdmin):
    list_display = [
        'candidat', 'bureau_vote', 'nombre_voix', 
        'representant', 'verifie', 'apercu_photo', 'date_saisie'
    ]
    list_filter = [
        'verifie', 'candidat', 'date_saisie',
        'bureau_vote__centre_vote__sous_prefecture__departement'
    ]
    search_fields = [
        'candidat__first_name', 'candidat__last_name',
        'bureau_vote__numero', 'bureau_vote__centre_vote__nom',
        'representant__first_name', 'representant__last_name'
    ]
    readonly_fields = ['date_saisie', 'date_modification', 'apercu_photo_large']
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('candidat', 'bureau_vote', 'representant', 'nombre_voix')
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
                '<img src="{}" style="max-width: 500px; max-height: 500px; border-radius: 8px;" />',
                obj.photo_pv.url
            )
        return 'Aucune photo'
    apercu_photo_large.short_description = "Aperçu du procès-verbal"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'candidat', 'representant', 'bureau_vote',
            'bureau_vote__centre_vote', 'bureau_vote__centre_vote__sous_prefecture'
        )


# Personnalisation du site admin
admin.site.site_header = "Administration Électorale"
admin.site.site_title = "Gestion des Résultats"
admin.site.index_title = "Tableau de bord"