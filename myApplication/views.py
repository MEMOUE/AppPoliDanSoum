from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.http import JsonResponse
from .models import Resultat, BureauVote, CentreVote, SousPrefecture, User
from .forms import LoginForm, ResultatForm


def home(request):
    """Page d'accueil"""
    context = {
        'total_bureaux': BureauVote.objects.count(),
        'total_centres': CentreVote.objects.count(),
        'total_sous_prefectures': SousPrefecture.objects.count(),
        'resultats_saisis': Resultat.objects.count(),
    }
    return render(request, 'myApplication/home.html', context)


def login_view(request):
    """Vue de connexion"""
    if request.user.is_authenticated:
        # Redirection selon le rôle
        if request.user.role == 'candidat':
            return redirect('dashboard_candidat')
        elif request.user.role == 'representant':
            return redirect('saisie_resultat')
        return redirect('home')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bienvenue {user.get_full_name()}!')
            
            # Redirection selon le rôle
            if user.role == 'candidat':
                return redirect('dashboard_candidat')
            elif user.role == 'representant':
                return redirect('saisie_resultat')
            
            return redirect('home')
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    else:
        form = LoginForm()
    
    return render(request, 'myApplication/login.html', {'form': form})


@login_required
def logout_view(request):
    """Vue de déconnexion"""
    logout(request)
    messages.info(request, 'Vous avez été déconnecté avec succès.')
    return redirect('home')


@login_required
def saisie_resultat(request):
    """Vue pour la saisie des résultats par les représentants"""
    # Vérifier que l'utilisateur est un représentant
    if request.user.role != 'representant':
        messages.error(request, 'Accès non autorisé. Cette page est réservée aux représentants.')
        return redirect('home')
    
    # Vérifier que le représentant a un bureau affecté
    if not request.user.bureau_vote:
        messages.error(request, 'Aucun bureau de vote ne vous est affecté. Contactez l\'administrateur.')
        return render(request, 'myApplication/saisie_resultat.html', {
            'no_bureau': True
        })
    
    bureau = request.user.bureau_vote
    
    # Récupérer tous les candidats
    candidats = User.objects.filter(role='candidat').order_by('first_name', 'last_name')
    
    # Récupérer les résultats déjà saisis pour ce bureau
    resultats_existants = Resultat.objects.filter(bureau_vote=bureau).select_related('candidat')
    resultats_dict = {r.candidat.id: r for r in resultats_existants}
    
    if request.method == 'POST':
        candidat_id = request.POST.get('candidat_id')
        candidat = get_object_or_404(User, id=candidat_id, role='candidat')
        
        # Vérifier si un résultat existe déjà
        resultat_existant = resultats_dict.get(candidat.id)
        
        form = ResultatForm(
            request.POST, 
            request.FILES,
            instance=resultat_existant,
            bureau_vote=bureau,
            candidat=candidat
        )
        
        if form.is_valid():
            resultat = form.save(commit=False)
            resultat.candidat = candidat
            resultat.bureau_vote = bureau
            resultat.representant = request.user
            resultat.save()
            
            action = "mis à jour" if resultat_existant else "enregistré"
            messages.success(
                request, 
                f'Résultat {action} avec succès pour {candidat.get_full_name()} : {resultat.nombre_voix} voix'
            )
            return redirect('saisie_resultat')
        else:
            messages.error(request, 'Erreur lors de la saisie. Veuillez vérifier les informations.')
            return render(request, 'myApplication/saisie_resultat.html', {
                'bureau': bureau,
                'candidats': candidats,
                'resultats_dict': resultats_dict,
                'form': form,
                'candidat_selectionne': candidat,
            })
    
    context = {
        'bureau': bureau,
        'candidats': candidats,
        'resultats_dict': resultats_dict,
        'form': ResultatForm(),
    }
    
    return render(request, 'myApplication/saisie_resultat.html', context)


@login_required
def dashboard_candidat(request):
    """Tableau de bord pour les candidats"""
    # Vérifier que l'utilisateur est un candidat
    if request.user.role != 'candidat':
        messages.error(request, 'Accès non autorisé. Cette page est réservée aux candidats.')
        return redirect('home')
    
    candidat = request.user
    
    # Récupérer tous les résultats du candidat
    resultats = Resultat.objects.filter(candidat=candidat).select_related(
        'bureau_vote',
        'bureau_vote__centre_vote',
        'bureau_vote__centre_vote__sous_prefecture',
        'bureau_vote__centre_vote__sous_prefecture__departement',
        'representant'
    ).order_by(
        'bureau_vote__centre_vote__sous_prefecture__nom',
        'bureau_vote__centre_vote__nom',
        'bureau_vote__numero'
    )
    
    # Statistiques globales
    total_voix = resultats.aggregate(Sum('nombre_voix'))['nombre_voix__sum'] or 0
    total_bureaux_avec_resultats = resultats.count()
    total_bureaux = BureauVote.objects.count()
    
    # Calculer le pourcentage de participation
    taux_couverture = (total_bureaux_avec_resultats / total_bureaux * 100) if total_bureaux > 0 else 0
    
    # Statistiques par sous-préfecture
    stats_sous_prefecture = {}
    for resultat in resultats:
        sous_pref = resultat.bureau_vote.centre_vote.sous_prefecture
        if sous_pref.id not in stats_sous_prefecture:
            stats_sous_prefecture[sous_pref.id] = {
                'nom': sous_pref.nom,
                'departement': sous_pref.departement.nom,
                'total_voix': 0,
                'nombre_bureaux': 0,
            }
        stats_sous_prefecture[sous_pref.id]['total_voix'] += resultat.nombre_voix
        stats_sous_prefecture[sous_pref.id]['nombre_bureaux'] += 1
    
    # Statistiques par centre de vote
    stats_centre = {}
    for resultat in resultats:
        centre = resultat.bureau_vote.centre_vote
        if centre.id not in stats_centre:
            stats_centre[centre.id] = {
                'nom': centre.nom,
                'sous_prefecture': centre.sous_prefecture.nom,
                'total_voix': 0,
                'nombre_bureaux': 0,
            }
        stats_centre[centre.id]['total_voix'] += resultat.nombre_voix
        stats_centre[centre.id]['nombre_bureaux'] += 1
    
    # Calculer le pourcentage (si on a les données de tous les candidats)
    # On suppose qu'on calcule par rapport au total des voix exprimées dans les bureaux où le candidat a des résultats
    bureaux_avec_resultats = [r.bureau_vote for r in resultats]
    total_voix_tous_candidats = Resultat.objects.filter(
        bureau_vote__in=bureaux_avec_resultats
    ).aggregate(Sum('nombre_voix'))['nombre_voix__sum'] or 0
    
    pourcentage = (total_voix / total_voix_tous_candidats * 100) if total_voix_tous_candidats > 0 else 0
    
    context = {
        'candidat': candidat,
        'resultats': resultats,
        'total_voix': total_voix,
        'total_bureaux_avec_resultats': total_bureaux_avec_resultats,
        'total_bureaux': total_bureaux,
        'taux_couverture': round(taux_couverture, 2),
        'pourcentage': round(pourcentage, 2),
        'stats_sous_prefecture': sorted(stats_sous_prefecture.values(), key=lambda x: x['total_voix'], reverse=True),
        'stats_centre': sorted(stats_centre.values(), key=lambda x: x['total_voix'], reverse=True),
    }
    
    return render(request, 'myApplication/dashboard_candidat.html', context)


@login_required
def detail_bureau(request, bureau_id):
    """Détail d'un bureau de vote (pour les candidats)"""
    if request.user.role != 'candidat':
        messages.error(request, 'Accès non autorisé.')
        return redirect('home')
    
    bureau = get_object_or_404(BureauVote, id=bureau_id)
    resultat = Resultat.objects.filter(
        candidat=request.user,
        bureau_vote=bureau
    ).select_related('representant').first()
    
    context = {
        'bureau': bureau,
        'resultat': resultat,
    }
    
    return render(request, 'myApplication/detail_bureau.html', context)