#!/usr/bin/env python3
"""
Upload RT-STRUCT processé vers Orthanc
Gère automatiquement les doublons et l'association à l'étude source
"""

import os
import sys
import pydicom
import requests
from pathlib import Path

# Configuration
ORTHANC_URL = "http://localhost:8042"
OUTPUT_DIR = Path("rt_diagnostic_output")

def upload_rtstruct_to_orthanc(file_path, force_reupload=False):
    """
    Upload un fichier RT-STRUCT vers Orthanc
    
    Args:
        file_path: Chemin vers le fichier DICOM
        force_reupload: Si True, supprime l'ancien et re-upload
    
    Returns:
        dict avec les infos de l'instance uploadée
    """
    
    # 1. Lire le fichier DICOM pour extraire les métadonnées
    print(f"📖 Lecture du fichier: {file_path}")
    ds = pydicom.dcmread(file_path)
    
    sop_instance_uid = ds.SOPInstanceUID
    study_instance_uid = ds.StudyInstanceUID
    series_instance_uid = ds.SeriesInstanceUID
    
    print(f"   SOP Instance UID: {sop_instance_uid}")
    print(f"   Study UID: {study_instance_uid}")
    print(f"   Series UID: {series_instance_uid}")
    
    # 2. Vérifier si l'instance existe déjà dans Orthanc
    lookup_url = f"{ORTHANC_URL}/tools/lookup"
    lookup_response = requests.post(lookup_url, data=sop_instance_uid)
    
    if lookup_response.status_code == 200 and lookup_response.json():
        existing_instances = lookup_response.json()
        print(f"\n⚠️  Instance déjà présente dans Orthanc: {existing_instances[0]['ID']}")
        
        if force_reupload:
            # Supprimer l'ancienne instance
            print("🗑️  Suppression de l'ancienne instance...")
            delete_url = f"{ORTHANC_URL}/instances/{existing_instances[0]['ID']}"
            requests.delete(delete_url)
            print("✅ Ancienne instance supprimée")
        else:
            print("💡 Utilisation de l'instance existante (utilisez force_reupload=True pour remplacer)")
            return {
                'ID': existing_instances[0]['ID'],
                'Path': existing_instances[0]['Path'],
                'Type': existing_instances[0]['Type'],
                'Status': 'existing'
            }
    
    # 3. Upload le fichier vers Orthanc
    print(f"\n📤 Upload vers Orthanc...")
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        upload_response = requests.post(f"{ORTHANC_URL}/instances", files=files)
    
    if upload_response.status_code != 200:
        print(f"❌ Erreur d'upload: {upload_response.status_code}")
        print(f"   Response: {upload_response.text}")
        return None
    
    # 4. Parser la réponse (peut être JSON ou vide si doublon)
    if upload_response.text.strip():
        try:
            result = upload_response.json()
            instance_id = result.get('ID')
        except:
            # Réponse non-JSON, probablement juste l'ID en texte
            instance_id = upload_response.text.strip()
    else:
        # Réponse vide = doublon, chercher l'ID via lookup
        print("   Réponse vide (doublon détecté), recherche de l'ID...")
        lookup_response = requests.post(lookup_url, data=sop_instance_uid)
        if lookup_response.status_code == 200 and lookup_response.json():
            instance_id = lookup_response.json()[0]['ID']
        else:
            print("❌ Impossible de trouver l'instance après upload")
            return None
    
    print(f"✅ Upload réussi! Instance ID: {instance_id}")
    
    # 5. Récupérer les informations complètes de l'instance
    instance_url = f"{ORTHANC_URL}/instances/{instance_id}"
    instance_info = requests.get(instance_url).json()
    
    series_id = instance_info['ParentSeries']
    
    # 6. Récupérer l'ID de l'étude via la série
    series_url = f"{ORTHANC_URL}/series/{series_id}"
    series_info = requests.get(series_url).json()
    
    study_id = series_info['ParentStudy']
    
    # 7. Afficher les informations de l'étude
    study_url = f"{ORTHANC_URL}/studies/{study_id}"
    study_info = requests.get(study_url).json()
    
    print(f"\n📊 Informations de l'upload:")
    print(f"   Patient: {study_info['PatientMainDicomTags'].get('PatientName', 'N/A')}")
    print(f"   Study Description: {study_info['MainDicomTags'].get('StudyDescription', 'N/A')}")
    print(f"   Series Description: {series_info['MainDicomTags'].get('SeriesDescription', 'N/A')}")
    print(f"   Modality: {series_info['MainDicomTags'].get('Modality', 'N/A')}")
    print(f"   Number of Instances in Series: {len(series_info['Instances'])}")
    
    print(f"\n🔗 URLs Orthanc:")
    print(f"   Study: {ORTHANC_URL}/app/explorer.html#study?uuid={study_id}")
    print(f"   Series: {ORTHANC_URL}/app/explorer.html#series?uuid={series_id}")
    print(f"   Instance: {ORTHANC_URL}/app/explorer.html#instance?uuid={instance_id}")
    
    return {
        'ID': instance_id,
        'ParentSeries': series_id,
        'ParentStudy': study_id,
        'Status': 'uploaded',
        'SeriesDescription': series_info['MainDicomTags'].get('SeriesDescription', 'N/A'),
        'PatientName': study_info['PatientMainDicomTags'].get('PatientName', 'N/A')
    }


def main():
    """Script principal"""
    
    print("=" * 70)
    print("🚀 Upload RT-STRUCT vers Orthanc")
    print("=" * 70)
    
    # Fichier par défaut
    default_file = OUTPUT_DIR / "rtstruct.dcm"
    
    # Vérifier l'option --force
    force = "--force" in sys.argv
    if force:
        sys.argv.remove("--force")
    
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
    else:
        file_path = default_file
    
    if not file_path.exists():
        print(f"❌ Fichier introuvable: {file_path}")
        print(f"\nUtilisation: python {sys.argv[0]} [chemin_vers_fichier.dcm] [--force]")
        return 1
    
    # Upload avec option de forcer le re-upload
    result = upload_rtstruct_to_orthanc(file_path, force_reupload=force)
    
    if result:
        print(f"\n✅ Upload terminé avec succès!")
        print(f"   Status: {result['Status']}")
        if result['Status'] == 'uploaded':
            print(f"   📍 Nouveau fichier uploadé dans Orthanc")
        else:
            print(f"   📍 Fichier déjà présent, réutilisé")
    else:
        print(f"\n❌ Échec de l'upload")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
