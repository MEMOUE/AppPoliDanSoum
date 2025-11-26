from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('connexion/', views.login_view, name='login'),
    path('deconnexion/', views.logout_view, name='logout'),
    path('saisie-resultat/', views.saisie_resultat, name='saisie_resultat'),
    path('dashboard-legacy/', views.dashboard_candidat, name='dashboard_candidat'),
    path('bureau/<int:bureau_id>/', views.detail_bureau, name='detail_bureau'),
    path('dashboard/', views.dashboard_general, name='dashboard_general'),

    # API - IMPORTANT : Cette ligne doit être présente
    path('api/sous-prefecture/<int:sous_prefecture_id>/bureaux/',
         views.api_sous_prefecture_bureaux,
         name='api_sous_prefecture_bureaux'),

    path('export/excel/', views.export_resultats_excel, name='export_resultats_excel'),
    path('export/pdf/', views.export_resultats_pdf, name='export_resultats_pdf'),
]