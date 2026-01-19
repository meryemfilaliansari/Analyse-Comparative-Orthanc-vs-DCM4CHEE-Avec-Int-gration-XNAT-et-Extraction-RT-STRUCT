#!/usr/bin/env python3
"""
⬆️ Upload Automatique RT-STRUCT vers Orthanc
============================================
Upload le fichier RT-STRUCT traité vers Orthanc
"""

import requests
import pydicom
from pathlib import Path
import json

ORTHANC_URL = "http://localhost:8042"

print("="*80)
print("⬆️ UPLOAD AUTOMATIQUE RT-STRUCT VERS ORTHANC")
print("="*80)

# Fichier à uploader
rtstruct_file = Path("rt_diagnostic_output/rtstruct.dcm")

if not rtstruct_file.exists():
    print(f"\n❌ Fichier non trouvé: {rtstruct_file}")
    exit(1)

print(f"\n📂 Fichier source: {rtstruct_file}")

# Lire les métadonnées DICOM
print("\n📋 Lecture des métadonnées DICOM...")
ds = pydicom.dcmread(str(rtstruct_file))

patient_name = str(ds.PatientName)
study_uid = ds.StudyInstanceUID
series_uid = ds.SeriesInstanceUID
sop_uid = ds.SOPInstanceUID

print(f"   Patient: {patient_name}")
print(f"   Study UID: {study_uid}")
print(f"   Series UID: {series_uid}")
print(f"   SOP Instance UID: {sop_uid}")

# Vérifier si déjà présent dans Orthanc
print("\n🔍 Vérification dans Orthanc...")
try:
    # Chercher par Study UID
    response = requests.post(
        f"{ORTHANC_URL}/tools/lookup",
        json=study_uid
    )
    
    if response.status_code == 200:
        results = response.json()
        if results:
            print(f"✅ Étude déjà présente dans Orthanc: {results[0]['ID'][:8]}...")
            
            # Chercher si cette instance spécifique existe
            instance_response = requests.post(
                f"{ORTHANC_URL}/tools/lookup",
                json=sop_uid
            )
            
            if instance_response.status_code == 200:
                instance_results = instance_response.json()
                if instance_results:
                    print(f"⚠️  Cette instance RT-STRUCT existe déjà dans Orthanc!")
                    print(f"   ID: {instance_results[0]['ID']}")
                    
                    choice = input("\nVoulez-vous quand même re-uploader? (o/n): ")
                    if choice.lower() not in ['o', 'oui', 'y', 'yes']:
                        print("\n❌ Upload annulé")
                        exit(0)
except Exception as e:
    print(f"⚠️  Impossible de vérifier: {e}")

# Upload vers Orthanc
print("\n⬆️ Upload vers Orthanc...")

try:
    with open(rtstruct_file, 'rb') as f:
        response = requests.post(
            f"{ORTHANC_URL}/instances",
            files={'file': f},
            headers={'Accept': 'application/json'}
        )
    
    if response.status_code == 200:
        result = response.json()
        
        print("✅ Upload réussi!")
        print(f"\n📊 Résultat:")
        print(f"   Instance ID: {result['ID']}")
        print(f"   Parent Series: {result['ParentSeries']}")
        print(f"   Parent Study: {result['ParentStudy']}")
        print(f"   Status: {result.get('Status', 'Success')}")
        
        # Récupérer les infos de l'étude
        study_id = result['ParentStudy']
        study_info = requests.get(f"{ORTHANC_URL}/studies/{study_id}").json()
        
        print(f"\n📋 Étude mise à jour:")
        print(f"   Patient: {study_info.get('PatientMainDicomTags', {}).get('PatientName', 'N/A')}")
        print(f"   Nombre de séries: {len(study_info.get('Series', []))}")
        
        # Lister les séries
        print(f"\n📂 Séries dans cette étude:")
        for series_id in study_info.get('Series', []):
            series_info = requests.get(f"{ORTHANC_URL}/series/{series_id}").json()
            modality = series_info.get('MainDicomTags', {}).get('Modality', 'Unknown')
            description = series_info.get('MainDicomTags', {}).get('SeriesDescription', 'N/A')
            num_instances = len(series_info.get('Instances', []))
            
            marker = "⭐" if series_id == result['ParentSeries'] else "  "
            print(f"   {marker} {modality}: {description} ({num_instances} instances)")
        
        # URLs de visualisation
        print(f"\n🌐 Visualiser dans:")
        print(f"   • Orthanc: http://localhost:8042/app/explorer.html#study?uuid={study_id}")
        print(f"   • OHIF: http://localhost:8042/ohif/viewer?StudyInstanceUIDs={study_uid}")
        
    elif response.status_code == 200:
        print("⚠️  Upload effectué mais le fichier existait déjà (pas de doublon créé)")
    else:
        print(f"❌ Erreur d'upload: {response.status_code}")
        print(f"   Message: {response.text}")
        
except Exception as e:
    print(f"❌ Erreur: {e}")
    exit(1)

print("\n" + "="*80)
print("✅ TERMINÉ")
print("="*80)
