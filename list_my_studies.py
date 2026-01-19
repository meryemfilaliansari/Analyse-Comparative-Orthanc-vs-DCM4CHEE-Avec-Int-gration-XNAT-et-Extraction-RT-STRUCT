#!/usr/bin/env python3
"""
📋 Liste de VOS Études DICOM dans Orthanc
==========================================
"""

import requests
import webbrowser
from collections import defaultdict

ORTHANC_URL = "http://localhost:8042"

print("="*80)
print("📋 VOS ÉTUDES DICOM DANS ORTHANC")
print("="*80)

# Récupérer toutes les études
studies = requests.get(f"{ORTHANC_URL}/studies").json()

print(f"\n✅ Total: {len(studies)} études trouvées\n")
print("="*80)

# Analyser chaque étude
studies_info = []

for i, study_id in enumerate(studies, 1):
    try:
        study_info = requests.get(f"{ORTHANC_URL}/studies/{study_id}").json()
        
        patient_name = study_info.get('PatientMainDicomTags', {}).get('PatientName', 'Unknown')
        study_date = study_info.get('MainDicomTags', {}).get('StudyDate', 'N/A')
        study_desc = study_info.get('MainDicomTags', {}).get('StudyDescription', 'N/A')
        
        # Compter les modalités
        modalities = []
        has_rtstruct = False
        has_seg = False
        
        for series_id in study_info.get('Series', []):
            series_info = requests.get(f"{ORTHANC_URL}/series/{series_id}").json()
            modality = series_info.get('MainDicomTags', {}).get('Modality', 'Unknown')
            modalities.append(modality)
            
            if modality == 'RTSTRUCT':
                has_rtstruct = True
            elif modality == 'SEG':
                has_seg = True
        
        # Compter les modalités
        modality_counts = {}
        for m in modalities:
            modality_counts[m] = modality_counts.get(m, 0) + 1
        
        modality_str = ", ".join([f"{k}({v})" for k, v in modality_counts.items()])
        
        studies_info.append({
            'index': i,
            'study_id': study_id,
            'patient': patient_name,
            'date': study_date,
            'description': study_desc,
            'modalities': modality_str,
            'has_rtstruct': has_rtstruct,
            'has_seg': has_seg,
            'num_series': len(study_info.get('Series', []))
        })
        
        # Afficher
        icon = "🎯" if has_rtstruct else ("📦" if has_seg else "📊")
        
        print(f"{icon} Étude {i}: {patient_name}")
        print(f"   Date: {study_date}")
        print(f"   Description: {study_desc}")
        print(f"   Modalités: {modality_str}")
        print(f"   Séries: {len(study_info.get('Series', []))}")
        
        if has_rtstruct:
            print(f"   ⭐ CONTIENT RT-STRUCT! ⭐")
        if has_seg:
            print(f"   ✨ CONTIENT DICOM-SEG! ✨")
        
        print()
        
    except Exception as e:
        print(f"⚠️  Erreur lecture étude {i}: {e}\n")

print("="*80)
print("📊 RÉSUMÉ")
print("="*80)

# Compter les études avec RT-STRUCT
rtstruct_studies = [s for s in studies_info if s['has_rtstruct']]
seg_studies = [s for s in studies_info if s['has_seg']]

print(f"\n✅ Total études: {len(studies_info)}")
print(f"🎯 Études avec RT-STRUCT: {len(rtstruct_studies)}")
print(f"📦 Études avec DICOM-SEG: {len(seg_studies)}")

# Patients uniques
unique_patients = set(s['patient'] for s in studies_info)
print(f"👤 Patients uniques: {len(unique_patients)}")

if rtstruct_studies:
    print("\n" + "="*80)
    print("🎯 ÉTUDES AVEC RT-STRUCT (Contours de structures)")
    print("="*80)
    
    for study in rtstruct_studies:
        print(f"\n{study['index']}. {study['patient']} - {study['date']}")
        print(f"   Description: {study['description']}")
        print(f"   Modalités: {study['modalities']}")
        print(f"   ID Orthanc: {study['study_id'][:12]}...")
        
        # URL pour visualiser
        print(f"\n   🔗 Visualiser dans Orthanc:")
        print(f"      http://localhost:8042/ui/app/#/studies/{study['study_id']}")
        
        print(f"\n   🎨 Visualiser dans OHIF:")
        print(f"      http://localhost:8042/ohif/viewer?StudyInstanceUIDs={study['study_id']}")

if seg_studies:
    print("\n" + "="*80)
    print("📦 ÉTUDES AVEC DICOM-SEG (Masques voxelisés)")
    print("="*80)
    
    for study in seg_studies:
        print(f"\n{study['index']}. {study['patient']} - {study['date']}")
        print(f"   Modalités: {study['modalities']}")

print("\n" + "="*80)
print("🚀 COMMENT VISUALISER")
print("="*80)

if rtstruct_studies:
    first_rtstruct = rtstruct_studies[0]
    
    print(f"\n📖 Pour voir votre RT-STRUCT ({first_rtstruct['patient']}):")
    print(f"\n1️⃣  INTERFACE ORTHANC (Simple):")
    print(f"   http://localhost:8042/ui/app/#/studies/{first_rtstruct['study_id']}")
    print(f"   → Cliquez sur la série RT-STRUCT")
    print(f"   → Voir les métadonnées et télécharger")
    
    print(f"\n2️⃣  OHIF VIEWER (Images médicales):")
    print(f"   http://localhost:8042/ohif/")
    print(f"   → Cherchez le patient: {first_rtstruct['patient']}")
    print(f"   → ATTENTION: OHIF ne supporte pas RT-STRUCT natif ❌")
    print(f"   → Il faut d'abord convertir en DICOM-SEG ✅")
    
    print(f"\n3️⃣  PYTHON LOCAL (Recommandé):")
    print(f"   python demo_rt_interactive.py")
    print(f"   → Affiche les masques déjà extraits")
    print(f"   → Navigation slice par slice")
    
    print(f"\n4️⃣  TÉLÉCHARGER ET OUVRIR AILLEURS:")
    print(f"   → Aller dans Orthanc UI")
    print(f"   → Télécharger la série RT-STRUCT")
    print(f"   → Ouvrir avec 3D Slicer Desktop, MIM, Eclipse, etc.")

print("\n💡 Astuce: Si vous voulez voir les contours dans OHIF,")
print("   il faut d'abord convertir RT-STRUCT → DICOM-SEG")
print("   (Service RT-Utils a un bug actuellement)")

print("\n" + "="*80)

# Demander si on veut ouvrir
if rtstruct_studies:
    print("\n🌐 Voulez-vous ouvrir l'interface Orthanc? (o/n)")
    choice = input(">>> ").lower()
    
    if choice == 'o' or choice == 'y' or choice == 'yes' or choice == 'oui':
        first = rtstruct_studies[0]
        url = f"http://localhost:8042/ui/app/#/studies/{first['study_id']}"
        print(f"\n✅ Ouverture: {url}")
        webbrowser.open(url)
    else:
        print("\n✅ OK, vous pouvez ouvrir manuellement les URLs ci-dessus")
else:
    print("\n⚠️  Aucune étude RT-STRUCT trouvée")
    print("   Vos études contiennent principalement des images CT/MR")
    print("   Pour voir vos images dans OHIF:")
    print("   http://localhost:8042/ohif/")
    
    print("\n🌐 Ouvrir OHIF maintenant? (o/n)")
    choice = input(">>> ").lower()
    
    if choice == 'o' or choice == 'y' or choice == 'yes' or choice == 'oui':
        webbrowser.open("http://localhost:8042/ohif/")
        print("✅ OHIF ouvert!")

print("\n" + "="*80)
print("✅ TERMINÉ")
print("="*80)
