#!/usr/bin/env python3
"""
🎨 Visualisation RT-STRUCT Simple avec 3D Slicer
================================================
Ce script ouvre automatiquement votre RT-STRUCT dans 3D Slicer
"""

import webbrowser
import requests
import time

ORTHANC_URL = "http://localhost:8042"
SLICER_URL = "http://localhost:3003"

print("="*70)
print("🎨 OUVERTURE DE 3D SLICER POUR RT-STRUCT")
print("="*70)

# Vérifier que 3D Slicer est accessible
print("\n🔍 Vérification de 3D Slicer...")
try:
    response = requests.get(SLICER_URL, timeout=5)
    if response.status_code == 200:
        print("✅ 3D Slicer est en ligne!")
    else:
        print(f"⚠️  3D Slicer répond avec le code: {response.status_code}")
except Exception as e:
    print(f"❌ 3D Slicer n'est pas accessible: {e}")
    print("\n💡 Solution:")
    print("   docker-compose -f docker-compose-rt-complete.yml up -d slicer-rt-web")
    exit(1)

# Vérifier Orthanc
print("\n🔍 Vérification d'Orthanc...")
try:
    response = requests.get(f"{ORTHANC_URL}/system", timeout=5)
    if response.status_code == 200:
        info = response.json()
        print(f"✅ Orthanc connecté: {info['Name']} v{info['Version']}")
    else:
        print("⚠️  Orthanc ne répond pas correctement")
except Exception as e:
    print(f"❌ Orthanc inaccessible: {e}")
    exit(1)

# Trouver le RT-STRUCT
print("\n🔍 Recherche du RT-STRUCT...")
studies = requests.get(f"{ORTHANC_URL}/studies").json()

rtstruct_study = None
for study_id in studies:
    try:
        study_info = requests.get(f"{ORTHANC_URL}/studies/{study_id}").json()
        
        for series_id in study_info.get('Series', []):
            series_info = requests.get(f"{ORTHANC_URL}/series/{series_id}").json()
            modality = series_info.get('MainDicomTags', {}).get('Modality', '')
            
            if modality == 'RTSTRUCT':
                rtstruct_study = {
                    'study_id': study_id,
                    'patient': study_info.get('PatientMainDicomTags', {}).get('PatientName', 'Unknown'),
                    'description': study_info.get('MainDicomTags', {}).get('StudyDescription', 'N/A'),
                    'date': study_info.get('MainDicomTags', {}).get('StudyDate', 'N/A')
                }
                break
    except:
        continue
    
    if rtstruct_study:
        break

if rtstruct_study:
    print(f"✅ RT-STRUCT trouvé!")
    print(f"   Patient: {rtstruct_study['patient']}")
    print(f"   Study: {rtstruct_study['description']}")
    print(f"   Date: {rtstruct_study['date']}")
else:
    print("❌ Aucun RT-STRUCT trouvé dans Orthanc")
    exit(1)

# Instructions pour l'utilisateur
print("\n" + "="*70)
print("📋 INSTRUCTIONS POUR 3D SLICER")
print("="*70)

print("\n3D Slicer va s'ouvrir dans votre navigateur.")
print("\n📖 Étapes à suivre:")
print("\n1️⃣  CHARGER LES DONNÉES:")
print("   • Cliquer sur: File → Add Data → Choose File(s) to Add")
print("   • OU: Module DICOM → Import")
print("   • OU: DICOMweb → Query/Retrieve from Orthanc")

print("\n2️⃣  CONFIGURER ORTHANC:")
print("   • URL: http://orthanc-admin:8042")
print("   • (Pas d'authentification nécessaire)")

print(f"\n3️⃣  CHERCHER L'ÉTUDE:")
print(f"   • Patient: {rtstruct_study['patient']}")
print(f"   • Date: {rtstruct_study['date']}")

print("\n4️⃣  CHARGER:")
print("   • Sélectionner la série CT")
print("   • Sélectionner le RT-STRUCT")
print("   • Cliquer 'Load'")

print("\n5️⃣  VISUALISER:")
print("   • Les contours RT s'affichent automatiquement en couleur!")
print("   • Utilisez les vues: Axial, Sagittal, Coronal, 3D")
print("   • Module 'Segment Editor' pour éditer")

print("\n" + "="*70)
print("🚀 OUVERTURE DE 3D SLICER...")
print("="*70)

# Ouvrir 3D Slicer
try:
    webbrowser.open(SLICER_URL)
    print(f"\n✅ 3D Slicer ouvert: {SLICER_URL}")
except Exception as e:
    print(f"\n⚠️  Erreur d'ouverture automatique: {e}")
    print(f"   Ouvrez manuellement: {SLICER_URL}")

print("\n💡 Astuce: Si 3D Slicer ne charge pas Orthanc:")
print("   → Utilisez 'Add Data' et uploadez les fichiers depuis:")
print("   → C:\\Users\\awati\\Desktop\\pacs\\rt_diagnostic_output\\rtstruct.dcm")

print("\n" + "="*70)
