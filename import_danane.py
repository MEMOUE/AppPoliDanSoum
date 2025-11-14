#!/usr/bin/env python
"""
Script d'importation des données électorales du département de DANANÉ
Pour utiliser ce script: python manage.py shell < import_danane.py
Ou: python import_danane.py (si vous ajoutez le setup Django ci-dessous)
"""

import os
import sys
import django

# Configuration Django (décommentez si vous exécutez le script directement)
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppLegislative.settings')
# django.setup()

from myApplication.models import Departement, SousPrefecture, CentreVote, BureauVote


def nettoyer_nom(nom):
    """Nettoie et formate un nom de lieu"""
    return nom.strip()


def importer_danane():
    """Import complet des données de Danané"""
    
    print("=" * 80)
    print("IMPORTATION DES DONNÉES DU DÉPARTEMENT DE DANANÉ")
    print("=" * 80)
    
    # 1. Créer ou récupérer le département
    departement, created = Departement.objects.get_or_create(
        code='DAN',
        defaults={
            'nom': 'DANANÉ'
        }
    )
    
    if created:
        print(f"\n✓ Département créé: {departement.nom}")
    else:
        print(f"\n✓ Département existant: {departement.nom}")
    
    # Données structurées par sous-préfecture
    donnees = {
        'DALEU': [
            ('EPP BLEUPLEU', ['01']),
            ('EPP BOUIMPLEU', ['01']),
            ('EPP DALEU 1', ['01', '02']),
            ('EPP DANTONGOUINE', ['01']),
            ('EPP DIEMPLEU', ['01', '02']),
            ('EPP DOUANGOPLEU', ['01', '02']),
            ('EPP DOUAPLEU', ['01']),
            ('EPP DOUELEU', ['01']),
            ('EPP GBANLEU', ['01', '02']),
            ('EPP GOPLEU', ['01']),
            ('EPP GOUEUPOUTA', ['01', '02']),
            ('EPP GUIZREU', ['01', '02']),
            ('EPP KATA', ['01']),
            ('EPP MLIMBA', ['01']),
            ('EPP NIMPLEU 1', ['01', '02']),
            ('EPP NIMPLEU 2', ['01']),
            ('EPP PAULKRO', ['01']),
            ('EPP SOUABA', ['01']),
            ('EPP YALEGBEUPLEU', ['01']),
            ('EPP YANGUILEU', ['01', '02']),
            ('EPP YASSEGOUINE', ['01', '02']),
            ('EPP ZEREGOUINE', ['01', '02']),
            ('EPP ZOUPLEU', ['01', '02', '03']),
            ('PLACE PUBLIQUE GBLINZEHIBA', ['01']),
            ('TIAPLEU', ['01']),
        ],
        'DANANE': [
            ('COLLEGE BABARA WELLER', ['01']),
            ('COLLEGE DIETY FELIX', ['01', '02', '03', '04']),
            ('COLLEGE LES MERITANTS', ['01']),
            ('COLLEGE PRIVE SANKHORE', ['01']),
            ('ECOLE FRANCO-ARABE', ['01', '02', '03']),
            ('ECOLE FRANCO-ARABE DE GONTIPLEU', ['01']),
            ('EPP BLIZREU', ['01']),
            ('EPP BOUAGLEU 1', ['01', '02']),
            ('EPP BOULEU', ['01']),
            ('EPP DEAGBALOUPLEU', ['01']),
            ('EPP DEAHOUEPLEU', ['01', '02']),
            ('EPP DIETTA', ['01']),
            ('EPP DIOTOUO', ['01']),
            ('EPP DIOULABOUGOU 2', ['01', '02', '03', '04', '05']),
            ('EPP DONGOUINE', ['01', '02']),
            ('EPP DOUGBOLEU', ['01']),
            ('EPP DRONGOUINE', ['01', '02']),
            ('EPP DRONGOUINE 2', ['01']),
            ('EPP GAHAPLEU', ['01']),
            ('EPP GANHIBA', ['01']),
            ('EPP GBALLEU', ['01']),
            ('EPP GBEUNTA', ['01']),
            ('EPP GOUALEU', ['01']),
            ('EPP GOUEGBEUPLEU', ['01']),
            ('EPP GUEIVILLE', ['01']),
            ('EPP GUIALOPLEU', ['01']),
            ('EPP GUIAPLEU', ['01']),
            ('EPP GUIN-HOUYE', ['01', '02']),
            ('EPP GUISSIPLEU', ['01']),
            ('EPP HOUPHOUETVILLE TP', ['01', '02']),
            ('EPP KEDERE', ['01']),
            ('EPP KINNEU', ['01']),
            ('EPP KOYATROGBEUPLEU', ['01']),
            ('EPP KPAKIEPLEU', ['01']),
            ('EPP LEKPEAVILLE', ['01']),
            ('EPP PEPLEU 2', ['01']),
            ('EPP SALEUPLEU', ['01']),
            ('EPP SALLEU', ['01']),
            ('EPP SIOBA', ['01']),
            ('EPP SOGALE', ['01', '02']),
            ('EPP TIEUKPOLOPLEU', ['01']),
            ('EPP TRODELEPLEU NANTA', ['01']),
            ('EPP TROKOLIMPLEU', ['01', '02']),
            ('EPP TROUIMPLEU', ['01']),
            ('EPP YELEU', ['01']),
            ('EPP YEPLEU', ['01']),
            ('EPP YOLEU', ['01']),
            ('EPP ZOLEU 1', ['01']),
            ('GROUPE SCOLAIRE COMMERCE', ['01', '02', '03']),
            ('GROUPE SCOLAIRE DANANE VILLAGE', ['01']),
            ('GROUPE SCOLAIRE GOUTRO', ['01']),
            ('GROUPE SCOLAIRE LAPLEU', ['01', '02']),
            ('GS BLESSALEU', ['01', '02', '03']),
            ('GS DIOULABOUGOU 1-3', ['01', '02', '03', '04', '05']),
            ('GS GNINGLEU', ['01', '02', '03', '04', '05', '06']),
            ('GS HOUPHOUET-VILLE', ['01', '02', '03', '04']),
            ('GS MISSION CATHOLIQUE', ['01', '02', '03', '04', '05']),
            ('GS MORIBADOUGOU', ['01', '02', '03', '04', '05']),
            ('GS PROTESTANT', ['01', '02', '03', '04']),
            ('JARDIN D\'ENFANTS', ['01', '02', '03']),
            ('LYCEE MODERNE ZINGBE MATHIAS', ['01', '02', '03']),
            ('MATERNELLE HOUPHOUETVILLE', ['01']),
            ('PLACE PUBLIC TOUAGOPLEU', ['01']),
            ('PLACE PUBLIQUE BEATRO', ['01']),
            ('PLACE PUBLIQUE BEHIPLEU', ['01']),
            ('PLACE PUBLIQUE DOUAPLEU', ['01']),
            ('PLACE PUBLIQUE GBEADAPLEU', ['01']),
            ('PLACE PUBLIQUE GOLEU', ['01']),
            ('PLACE PUBLIQUE KANAPLEU', ['01']),
            ('PLACE PUBLIQUE KPANGUIDOUOPLEU', ['01']),
            ('PLACE PUBLIQUE MOUATOUO', ['01']),
            ('PLACE PUBLIQUE OUYALEU', ['01']),
            ('PLACE PUBLIQUE TROZANDEPLEU', ['01']),
            ('PLACE PUBLIQUE ZOLEU 2', ['01']),
        ],
        'GBON-HOUYE': [
            ('EPP BIEUPLEU', ['01']),
            ('EPP BONTRO', ['01']),
            ('EPP DANIPLEU', ['01', '02']),
            ('EPP DANKOUAMPLEU', ['01']),
            ('EPP DOUALEU', ['01']),
            ('EPP GBANTOPLEU', ['01']),
            ('EPP GBETA', ['01']),
            ('EPP GBON-HOUYE', ['01', '02']),
            ('EPP GUIAN-HOUYE', ['01']),
            ('EPP KANTA-YOLE', ['01']),
            ('EPP KPON-HOUYE', ['01']),
            ('EPP TOUOPLEU', ['01']),
            ('EPP YEALE', ['01']),
            ('GROUPE SCOLAIRE GLAN-HOUYE', ['01', '02']),
            ('PLACE PUBLIQUE DROPLEU 2', ['01']),
            ('PLACE PUBLIQUE GNINGLIPLEU', ['01']),
        ],
        'KOUAN-HOULE': [
            ('EPP BAMPLEU', ['01']),
            ('EPP BOUAN-HOUYE', ['01']),
            ('EPP DOHOUBA', ['01']),
            ('EPP FEAPLEU', ['01']),
            ('EPP FLAMPLEU 2', ['01']),
            ('EPP GBATA', ['01']),
            ('EPP GOPOUPLEU', ['01']),
            ('EPP GOUELEU', ['01']),
            ('EPP GUETTA', ['01']),
            ('EPP GUEUPLEU', ['01']),
            ('EPP GUEUTAGBEUPLEU', ['01']),
            ('EPP GUEUTEAGBEUPLEU', ['01']),
            ('EPP KOHIBA', ['01']),
            ('EPP KOUAN HOULE 3', ['01']),
            ('EPP KPOLEU', ['01']),
            ('EPP LAMPLEU', ['01']),
            ('EPP NATTA', ['01']),
            ('EPP OUMPLEUPLEU', ['01']),
            ('EPP SORYDOUGOU', ['01']),
            ('EPP TIEPLEU 2', ['01']),
            ('EPP TIEUPLEU 1', ['01']),
            ('EPP ZANKAGLEU', ['01']),
            ('EPP ZEALE', ['01', '02']),
            ('GROUPE SCOLAIRE GBAPLEU', ['01']),
            ('GROUPE SCOLAIRE KPANPLEU-SIN-HOUYE', ['01', '02']),
            ('GS KOUAN-HOULE', ['01', '02', '03', '04']),
            ('PLACE PUBLIQUE GBLEUPLEU', ['01']),
            ('PLACE PUBLIQUE MAMPLEU', ['01']),
        ],
        'SEILEU': [
            ('EPP DOPLEU', ['01']),
            ('EPP FIEUPLEU', ['01']),
            ('EPP GUEUDOLOUPLEU', ['01']),
            ('EPP KPANZEGUEPLEU', ['01']),
            ('EPP MESSAMPLEU', ['01']),
            ('EPP SOHOUPLEU', ['01']),
            ('EPP TONNONTOUO', ['01']),
            ('EPP TRON-HOUNIEN', ['01']),
            ('EPP VIPLEU', ['01']),
            ('EPP YOTTA', ['01']),
            ('EPP ZAN-HOUNIEN', ['01']),
            ('EPP ZANGBATOUO', ['01']),
            ('EPP ZEUGUETOUO', ['01']),
            ('GROUPE SCOLAIRE BOUNTA', ['01', '02']),
            ('GROUPE SCOLAIRE GNIAMPLEU', ['01', '02']),
            ('GROUPE SCOLAIRE KANTA', ['01', '02']),
            ('GROUPE SCOLAIRE SEILEU', ['01', '02', '03']),
            ('PLACE PUBLIQUE BANZANDEPLEU', ['01']),
            ('PLACE PUBLIQUE DOUATOUO', ['01']),
            ('PLACE PUBLIQUE KONGATOUO', ['01']),
            ('PLACE PUBLIQUE KPEAPLEU', ['01']),
            ('PLACE PUBLIQUE LOLLEU', ['01']),
            ('PLACE PUBLIQUE YELLEU', ['01']),
        ],
    }
    
    # Compteurs pour les statistiques
    total_sous_prefectures = 0
    total_centres = 0
    total_bureaux = 0
    
    # 2. Importer les sous-préfectures, centres et bureaux
    for nom_sous_pref, centres_data in donnees.items():
        # Créer la sous-préfecture
        sous_prefecture, sp_created = SousPrefecture.objects.get_or_create(
            nom=nettoyer_nom(nom_sous_pref),
            departement=departement
        )
        
        if sp_created:
            total_sous_prefectures += 1
            print(f"\n🟩 Sous-préfecture créée: {sous_prefecture.nom}")
        else:
            print(f"\n🟩 Sous-préfecture existante: {sous_prefecture.nom}")
        
        bureaux_sous_pref = 0
        
        # Créer les centres de vote
        for nom_centre, numeros_bureaux in centres_data:
            centre, c_created = CentreVote.objects.get_or_create(
                nom=nettoyer_nom(nom_centre),
                sous_prefecture=sous_prefecture
            )
            
            if c_created:
                total_centres += 1
                print(f"   🏫 Centre créé: {centre.nom}")
            
            # Créer les bureaux de vote
            for numero in numeros_bureaux:
                bureau, b_created = BureauVote.objects.get_or_create(
                    numero=numero,
                    centre_vote=centre,
                    defaults={
                        'nombre_inscrits': 0  # À mettre à jour plus tard
                    }
                )
                
                if b_created:
                    total_bureaux += 1
                    bureaux_sous_pref += 1
        
        print(f"   ✓ Total bureaux dans {sous_prefecture.nom}: {bureaux_sous_pref}")
    
    # 3. Afficher les statistiques finales
    print("\n" + "=" * 80)
    print("STATISTIQUES D'IMPORTATION")
    print("=" * 80)
    print(f"✅ Département: {departement.nom}")
    print(f"✅ Sous-préfectures créées: {total_sous_prefectures}")
    print(f"✅ Centres de vote créés: {total_centres}")
    print(f"✅ Bureaux de vote créés: {total_bureaux}")
    print("\n" + "=" * 80)
    print("VÉRIFICATION DES DONNÉES")
    print("=" * 80)
    
    # Vérification par sous-préfecture
    for sous_pref in SousPrefecture.objects.filter(departement=departement):
        nb_centres = sous_pref.centres_vote.count()
        nb_bureaux = BureauVote.objects.filter(
            centre_vote__sous_prefecture=sous_pref
        ).count()
        print(f"{sous_pref.nom:20} → {nb_centres:3} centres, {nb_bureaux:3} bureaux")
    
    print("\n✅ Importation terminée avec succès!")
    print(f"✅ TOTAL: 240 bureaux de vote créés pour le département de DANANÉ")
    

if __name__ == '__main__':
    try:
        importer_danane()
    except Exception as e:
        print(f"\n❌ ERREUR lors de l'importation: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)