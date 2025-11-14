from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('connexion/', views.login_view, name='login'),
    path('deconnexion/', views.logout_view, name='logout'),
    path('saisie-resultat/', views.saisie_resultat, name='saisie_resultat'),
    path('dashboard/', views.dashboard_candidat, name='dashboard_candidat'),
    path('bureau/<int:bureau_id>/', views.detail_bureau, name='detail_bureau'),
]