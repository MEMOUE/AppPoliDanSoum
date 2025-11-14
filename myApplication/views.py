from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, F, Avg
from django.forms import formset_factory
from django.db import transaction
from .models import (
    ProcesVerbal, ResultatCandidat, BureauVote, 
    CentreVote, SousPrefecture, User
)
from .forms import LoginForm, ProcesVerbalForm, ResultatCandidatForm, ResultatCandidatFormSet


def home(request):
    """Page d'accueil"""
    context = {
        'total_bureaux': BureauVote.objects.count(),
        'total_centres': CentreVote.objects.count(),
        'total_sous_prefectures': SousPrefecture.objects.count(),
        'resultats_saisis': ProcesVerbal.objects.count(),
        'total_candidats': User.objects.filter(role='candidat').count(),
    }
    return render(request, "home.html", context)


def login_view(request):
    """Vue de connexion"""
    if request.user.is_authenticated:
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
            
            if user.role == 'candidat':
                return redirect('dashboard_candidat')
            elif user.role == 'representant':
                return redirect('saisie_resultat')
            
            return redirect('home')
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})


@login_required
def logout_view(request):
    """Vue de déconnexion"""
    logout(request)
    messages.info(request, 'Vous avez été déconnecté avec succès.')
    return redirect('home')


@login_required
def saisie_resultat(request):
    """Vue pour la saisie complète du procès-verbal par les représentants"""
    # Vérifier que l'utilisateur est un représentant
    if request.user.role != 'representant':
        messages.error(request, 'Accès non autorisé. Cette page est réservée aux représentants.')
        return redirect('home')
    
    # Vérifier que le représentant a un bureau affecté
    if not request.user.bureau_vote:
        return render(request, 'saisie_resultat.html', {'no_bureau': True})
    
    bureau = request.user.bureau_vote
    
    # Récupérer tous les candidats
    candidats = User.objects.filter(role='candidat').order_by('numero_candidat', 'first_name')
    
    if not candidats.exists():
        messages.error(request, 'Aucun candidat n\'est enregistré dans le système.')
        return redirect('home')
    
    # Récupérer le PV existant s'il existe
    try:
        pv_existant = ProcesVerbal.objects.get(bureau_vote=bureau)
    except ProcesVerbal.DoesNotExist:
        pv_existant = None
    
    # Créer le formset pour les résultats des candidats
    ResultatFormSet = formset_factory(
        ResultatCandidatForm, 
        formset=ResultatCandidatFormSet,
        extra=0
    )
    
    if request.method == 'POST':
        pv_form = ProcesVerbalForm(
            request.POST, 
            request.FILES, 
            instance=pv_existant,
            bureau_vote=bureau
        )
        
        # Récupérer le nombre d'inscrits du formulaire
        nombre_inscrits_saisi = request.POST.get('nombre_inscrits', 0)
        try:
            nombre_inscrits_saisi = int(nombre_inscrits_saisi)
        except (ValueError, TypeError):
            nombre_inscrits_saisi = 0
        
        # Calculer les suffrages exprimés pour la validation
        nombre_votants = int(request.POST.get('nombre_votants', 0))
        bulletins_nuls = int(request.POST.get('bulletins_nuls', 0))
        bulletins_blancs = int(request.POST.get('bulletins_blancs', 0))
        suffrages_exprimes = nombre_votants - bulletins_nuls - bulletins_blancs
        
        # Préparer les données initiales pour le formset
        formset_data = request.POST.copy()
        formset_data['form-TOTAL_FORMS'] = str(len(candidats))
        formset_data['form-INITIAL_FORMS'] = '0'
        formset_data['form-MIN_NUM_FORMS'] = '0'
        formset_data['form-MAX_NUM_FORMS'] = str(len(candidats))
        
        resultat_formset = ResultatFormSet(
            formset_data,
            proces_verbal=pv_existant,
            suffrages_exprimes=suffrages_exprimes
        )
        
        if pv_form.is_valid() and resultat_formset.is_valid():
            try:
                with transaction.atomic():
                    # Mettre à jour le nombre d'inscrits du bureau
                    bureau.nombre_inscrits = nombre_inscrits_saisi
                    bureau.save()
                    
                    # Sauvegarder le PV
                    pv = pv_form.save(commit=False)
                    pv.bureau_vote = bureau
                    pv.representant = request.user
                    pv.save()
                    
                    # Supprimer les anciens résultats
                    ResultatCandidat.objects.filter(proces_verbal=pv).delete()
                    
                    # Sauvegarder les résultats des candidats
                    for i, (form, candidat) in enumerate(zip(resultat_formset.forms, candidats)):
                        if form.is_valid() and form.cleaned_data:
                            nombre_voix = form.cleaned_data.get('nombre_voix', 0)
                            ResultatCandidat.objects.create(
                                proces_verbal=pv,
                                candidat=candidat,
                                nombre_voix=nombre_voix
                            )
                    
                    action = "mis à jour" if pv_existant else "enregistré"
                    messages.success(
                        request,
                        f'✅ Procès-verbal {action} avec succès ! '
                        f'{nombre_inscrits_saisi} inscrits, {pv.nombre_votants} votants, {pv.suffrages_exprimes} suffrages exprimés.'
                    )
                    return redirect('saisie_resultat')
                    
            except Exception as e:
                messages.error(request, f'Erreur lors de la sauvegarde : {str(e)}')
        else:
            if not pv_form.is_valid():
                for field, errors in pv_form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
            if not resultat_formset.is_valid():
                for error in resultat_formset.non_form_errors():
                    messages.error(request, error)
    
    else:
        pv_form = ProcesVerbalForm(instance=pv_existant, bureau_vote=bureau)
        
        # Préparer les données initiales pour le formset
        initial_data = []
        if pv_existant:
            for candidat in candidats:
                resultat = ResultatCandidat.objects.filter(
                    proces_verbal=pv_existant,
                    candidat=candidat
                ).first()
                initial_data.append({
                    'nombre_voix': resultat.nombre_voix if resultat else 0
                })
        else:
            initial_data = [{'nombre_voix': 0} for _ in candidats]
        
        resultat_formset = ResultatFormSet(
            initial=initial_data,
            proces_verbal=pv_existant
        )
    
    # Combiner candidats avec leurs formulaires
    candidats_forms = list(zip(candidats, resultat_formset))
    
    context = {
        'bureau': bureau,
        'pv_form': pv_form,
        'pv_existant': pv_existant,
        'candidats_forms': candidats_forms,
        'formset': resultat_formset,
        'management_form': resultat_formset.management_form,
    }
    
    return render(request, 'saisie_resultat.html', context)


@login_required
def dashboard_candidat(request):
    """Tableau de bord pour un candidat - Vue de ses résultats"""
    if request.user.role != 'candidat':
        messages.error(request, 'Accès non autorisé. Cette page est réservée aux candidats.')
        return redirect('home')
    
    candidat = request.user
    
    # Récupérer tous les résultats du candidat
    resultats = ResultatCandidat.objects.filter(
        candidat=candidat
    ).select_related(
        'proces_verbal',
        'proces_verbal__bureau_vote',
        'proces_verbal__bureau_vote__centre_vote',
        'proces_verbal__bureau_vote__centre_vote__sous_prefecture',
        'proces_verbal__bureau_vote__centre_vote__sous_prefecture__departement'
    ).order_by(
        'proces_verbal__bureau_vote__centre_vote__sous_prefecture__nom',
        'proces_verbal__bureau_vote__centre_vote__nom',
        'proces_verbal__bureau_vote__numero'
    )
    
    # Statistiques globales
    total_voix = resultats.aggregate(Sum('nombre_voix'))['nombre_voix__sum'] or 0
    total_bureaux_avec_resultats = resultats.count()
    total_bureaux = BureauVote.objects.count()
    
    # Calculer le total des suffrages exprimés
    pvs = ProcesVerbal.objects.filter(
        resultats__candidat=candidat
    ).distinct()
    
    total_suffrages_exprimes = pvs.aggregate(Sum('suffrages_exprimes'))['suffrages_exprimes__sum'] or 0
    total_votants = pvs.aggregate(Sum('nombre_votants'))['nombre_votants__sum'] or 0
    total_inscrits = sum([pv.bureau_vote.nombre_inscrits for pv in pvs])
    
    # Calculs des taux
    taux_couverture = (total_bureaux_avec_resultats / total_bureaux * 100) if total_bureaux > 0 else 0
    pourcentage_voix = (total_voix / total_suffrages_exprimes * 100) if total_suffrages_exprimes > 0 else 0
    taux_participation = (total_votants / total_inscrits * 100) if total_inscrits > 0 else 0
    
    # Statistiques par sous-préfecture
    stats_sous_prefecture = {}
    for resultat in resultats:
        sous_pref = resultat.proces_verbal.bureau_vote.centre_vote.sous_prefecture
        if sous_pref.id not in stats_sous_prefecture:
            stats_sous_prefecture[sous_pref.id] = {
                'nom': sous_pref.nom,
                'departement': sous_pref.departement.nom,
                'total_voix': 0,
                'nombre_bureaux': 0,
                'suffrages_exprimes': 0,
            }
        stats_sous_prefecture[sous_pref.id]['total_voix'] += resultat.nombre_voix
        stats_sous_prefecture[sous_pref.id]['nombre_bureaux'] += 1
        stats_sous_prefecture[sous_pref.id]['suffrages_exprimes'] += resultat.proces_verbal.suffrages_exprimes
    
    # Ajouter le pourcentage par sous-préfecture
    for sp_id in stats_sous_prefecture:
        sp = stats_sous_prefecture[sp_id]
        sp['pourcentage'] = (sp['total_voix'] / sp['suffrages_exprimes'] * 100) if sp['suffrages_exprimes'] > 0 else 0
    
    # Statistiques par centre de vote (Top 10)
    stats_centre = {}
    for resultat in resultats:
        centre = resultat.proces_verbal.bureau_vote.centre_vote
        if centre.id not in stats_centre:
            stats_centre[centre.id] = {
                'nom': centre.nom,
                'sous_prefecture': centre.sous_prefecture.nom,
                'total_voix': 0,
                'nombre_bureaux': 0,
                'suffrages_exprimes': 0,
            }
        stats_centre[centre.id]['total_voix'] += resultat.nombre_voix
        stats_centre[centre.id]['nombre_bureaux'] += 1
        stats_centre[centre.id]['suffrages_exprimes'] += resultat.proces_verbal.suffrages_exprimes
    
    # Ajouter le pourcentage par centre
    for c_id in stats_centre:
        c = stats_centre[c_id]
        c['pourcentage'] = (c['total_voix'] / c['suffrages_exprimes'] * 100) if c['suffrages_exprimes'] > 0 else 0
    
    context = {
        'candidat': candidat,
        'resultats': resultats,
        'total_voix': total_voix,
        'total_suffrages_exprimes': total_suffrages_exprimes,
        'total_votants': total_votants,
        'total_inscrits': total_inscrits,
        'total_bureaux_avec_resultats': total_bureaux_avec_resultats,
        'total_bureaux': total_bureaux,
        'taux_couverture': round(taux_couverture, 2),
        'pourcentage_voix': round(pourcentage_voix, 2),
        'taux_participation': round(taux_participation, 2),
        'stats_sous_prefecture': sorted(stats_sous_prefecture.values(), key=lambda x: x['total_voix'], reverse=True),
        'stats_centre': sorted(stats_centre.values(), key=lambda x: x['total_voix'], reverse=True)[:10],
    }
    
    return render(request, 'dashboard_candidat.html', context)


@login_required
def detail_bureau(request, bureau_id):
    """Détail d'un bureau de vote"""
    if request.user.role != 'candidat':
        messages.error(request, 'Accès non autorisé.')
        return redirect('home')
    
    bureau = get_object_or_404(BureauVote, id=bureau_id)
    pv = ProcesVerbal.objects.filter(bureau_vote=bureau).first()
    
    resultats_bureau = []
    if pv:
        resultats_bureau = ResultatCandidat.objects.filter(
            proces_verbal=pv
        ).select_related('candidat').order_by('-nombre_voix')
    
    context = {
        'bureau': bureau,
        'pv': pv,
        'resultats_bureau': resultats_bureau,
        'candidat': request.user,
    }
    
    return render(request, 'detail_bureau.html', context)