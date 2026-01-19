#!/usr/bin/env python3
"""
🔄 Workflow Automatique RT-STRUCT
==================================
1. Télécharge RT-STRUCT depuis Orthanc
2. Traite/Modifie si nécessaire
3. Re-upload automatiquement dans Orthanc
"""

import requests
import pydicom
import numpy as np
from pathlib import Path
import json
from datetime import datetime

ORTHANC_URL = "http://localhost:8042"
WORK_DIR = Path("rt_diagnostic_output")
WORK_DIR.mkdir(exist_ok=True)

class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_step(num, title):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}ÉTAPE {num}: {title}{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}\n")

def find_rtstruct():
    """Trouve un RT-STRUCT dans Orthanc"""
    print("🔍 Recherche d'un RT-STRUCT dans Orthanc...")
    
    studies = requests.get(f"{ORTHANC_URL}/studies").json()
    
    for study_id in studies:
        try:
            study_info = requests.get(f"{ORTHANC_URL}/studies/{study_id}").json()
            
            for series_id in study_info.get('Series', []):
                series_info = requests.get(f"{ORTHANC_URL}/series/{series_id}").json()
                modality = series_info.get('MainDicomTags', {}).get('Modality', '')
                
                if modality == 'RTSTRUCT':
                    instances = series_info.get('Instances', [])
                    if instances:
                        return {
                            'instance_id': instances[0],
                            'series_id': series_id,
                            'study_id': study_id,
                            'patient': study_info.get('PatientMainDicomTags', {}).get('PatientName', 'Unknown')
                        }
        except:
            continue
    
    return None

def download_rtstruct(instance_id, output_path):
    """Télécharge le RT-STRUCT depuis Orthanc"""
    print(f"📥 Téléchargement de l'instance {instance_id[:8]}...")
    
    url = f"{ORTHANC_URL}/instances/{instance_id}/file"
    response = requests.get(url)
    
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"✅ Téléchargé: {output_path}")
        return True
    else:
        print(f"❌ Erreur {response.status_code}")
        return False

def analyze_rtstruct(dicom_path):
    """Analyse le RT-STRUCT"""
    print("📋 Analyse du RT-STRUCT...")
    
    ds = pydicom.dcmread(str(dicom_path))
    
    rois = []
    if hasattr(ds, 'StructureSetROISequence'):
        for roi in ds.StructureSetROISequence:
            rois.append({
                'number': roi.ROINumber,
                'name': roi.ROIName
            })
    
    info = {
        'patient': str(ds.PatientName),
        'study_date': str(ds.StudyDate),
        'study_uid': str(ds.StudyInstanceUID),
        'series_uid': str(ds.SeriesInstanceUID),
        'sop_uid': str(ds.SOPInstanceUID),
        'num_rois': len(rois),
        'roi_names': [roi['name'] for roi in rois]
    }
    
    print(f"   Patient: {info['patient']}")
    print(f"   Date: {info['study_date']}")
    print(f"   ROIs: {', '.join(info['roi_names'])}")
    
    return ds, info

def modify_rtstruct(ds, modifications=None):
    """
    Modifie le RT-STRUCT (optionnel)
    
    Exemples de modifications possibles:
    - Changer les noms de ROIs
    - Ajouter des métadonnées
    - Modifier les couleurs
    """
    print("🔧 Application des modifications...")
    
    if modifications is None:
        modifications = {}
    
    # Exemple: Ajouter une annotation
    if not hasattr(ds, 'SeriesDescription'):
        ds.SeriesDescription = "RT-STRUCT Processed"
    else:
        if "Processed" not in ds.SeriesDescription:
            ds.SeriesDescription += " - Processed"
    
    # Exemple: Ajouter un timestamp
    processing_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Vous pouvez ajouter d'autres modifications ici
    # Par exemple: renommer des ROIs, modifier des couleurs, etc.
    
    print(f"✅ Modifications appliquées")
    print(f"   Description: {ds.SeriesDescription}")
    
    return ds

def save_modified_rtstruct(ds, output_path):
    """Sauvegarde le RT-STRUCT modifié"""
    print(f"💾 Sauvegarde du fichier modifié...")
    
    ds.save_as(str(output_path))
    print(f"✅ Sauvegardé: {output_path}")

def upload_to_orthanc(dicom_path):
    """Upload le fichier vers Orthanc avec gestion des doublons"""
    print(f"⬆️ Upload vers Orthanc...")
    
    # Lire les métadonnées DICOM pour gérer les doublons
    ds = pydicom.dcmread(dicom_path)
    sop_instance_uid = ds.SOPInstanceUID
    
    with open(dicom_path, 'rb') as f:
        response = requests.post(
            f"{ORTHANC_URL}/instances",
            files={'file': f}
        )
    
    if response.status_code == 200:
        instance_id = None
        
        # Gérer les différents types de réponse d'Orthanc
        if response.text.strip():
            try:
                result = response.json()
                instance_id = result.get('ID')
            except:
                # Texte simple = ID de l'instance
                instance_id = response.text.strip().strip('"')
        else:
            # Réponse vide = doublon, rechercher via lookup
            print("   (Doublon détecté, recherche de l'instance existante...)")
            lookup_response = requests.post(
                f"{ORTHANC_URL}/tools/lookup",
                data=sop_instance_uid
            )
            if lookup_response.status_code == 200 and lookup_response.json():
                instance_id = lookup_response.json()[0]['ID']
        
        if instance_id:
            # Récupérer les informations complètes via Instance → Series → Study
            instance_info = requests.get(f"{ORTHANC_URL}/instances/{instance_id}").json()
            series_info = requests.get(f"{ORTHANC_URL}/series/{instance_info['ParentSeries']}").json()
            study_info = requests.get(f"{ORTHANC_URL}/studies/{series_info['ParentStudy']}").json()
            
            print("✅ Upload réussi!")
            return {
                'ID': instance_id,
                'ParentSeries': instance_info['ParentSeries'],
                'ParentStudy': series_info['ParentStudy'],
                'PatientName': study_info['PatientMainDicomTags'].get('PatientName', 'N/A'),
                'SeriesDescription': series_info['MainDicomTags'].get('SeriesDescription', 'N/A')
            }
        else:
            print("❌ Impossible de trouver l'instance uploadée")
            return None
    else:
        print(f"❌ Erreur {response.status_code}: {response.text}")
        return None

def main():
    print(f"{Colors.BOLD}{Colors.GREEN}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║         🔄 WORKFLOW AUTOMATIQUE RT-STRUCT                         ║")
    print("║   Téléchargement → Traitement → Upload vers Orthanc              ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")
    
    # ÉTAPE 1: Rechercher RT-STRUCT
    print_step(1, "RECHERCHE DU RT-STRUCT DANS ORTHANC")
    
    rtstruct = find_rtstruct()
    
    if not rtstruct:
        print("❌ Aucun RT-STRUCT trouvé dans Orthanc")
        return
    
    print(f"✅ RT-STRUCT trouvé!")
    print(f"   Patient: {rtstruct['patient']}")
    print(f"   Instance ID: {rtstruct['instance_id'][:8]}...")
    
    # ÉTAPE 2: Télécharger
    print_step(2, "TÉLÉCHARGEMENT DEPUIS ORTHANC")
    
    original_file = WORK_DIR / "rtstruct_original.dcm"
    
    if not download_rtstruct(rtstruct['instance_id'], original_file):
        print("❌ Échec du téléchargement")
        return
    
    # ÉTAPE 3: Analyser
    print_step(3, "ANALYSE DU RT-STRUCT")
    
    ds, info = analyze_rtstruct(original_file)
    
    # Sauvegarder les métadonnées
    metadata_file = WORK_DIR / "workflow_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(info, f, indent=2)
    print(f"💾 Métadonnées sauvegardées: {metadata_file}")
    
    # ÉTAPE 4: Modifier (optionnel)
    print_step(4, "MODIFICATION DU RT-STRUCT (optionnel)")
    
    print("💡 Voulez-vous modifier le RT-STRUCT avant de le re-uploader?")
    print("   (Par exemple: ajouter des annotations, modifier des métadonnées)")
    choice = input("\nModifier? (o/n): ").lower()
    
    if choice in ['o', 'oui', 'y', 'yes']:
        ds_modified = modify_rtstruct(ds)
        modified_file = WORK_DIR / "rtstruct_modified.dcm"
        save_modified_rtstruct(ds_modified, modified_file)
        file_to_upload = modified_file
    else:
        print("⏭️ Aucune modification - utilisation du fichier original")
        file_to_upload = original_file
    
    # ÉTAPE 5: Re-upload vers Orthanc
    print_step(5, "RE-UPLOAD VERS ORTHANC")
    
    result = upload_to_orthanc(file_to_upload)
    
    if result:
        print(f"\n📊 Résultat de l'upload:")
        print(f"   Instance ID: {result['ID']}")
        print(f"   Study ID: {result['ParentStudy']}")
        print(f"   Series ID: {result['ParentSeries']}")
        print(f"   Patient: {result['PatientName']}")
        print(f"   Series Description: {result['SeriesDescription']}")
        
        print(f"\n🔗 URL Orthanc:")
        print(f"   {ORTHANC_URL}/app/explorer.html#study?uuid={result['ParentStudy']}")
    else:
        print("❌ Échec de l'upload")
        return
    
    # Vérifier que c'est bien dans la même étude
    if result['ParentStudy'] == rtstruct.get('study_id'):
        print(f"\n✅ Confirmé: RT-STRUCT uploadé dans la même étude!")
    else:
        print(f"\n⚠️  Note: Vérifier l'étude d'origine")
    
    # ÉTAPE 6: Résumé
    print_step(6, "RÉSUMÉ DU WORKFLOW")
    
    print("✅ Workflow terminé avec succès!")
    print(f"\n📂 Fichiers créés:")
    print(f"   • {original_file}")
    if file_to_upload != original_file:
        print(f"   • {file_to_upload}")
    print(f"   • {metadata_file}")
    
    print(f"\n📊 Statistiques:")
    print(f"   Patient: {info['patient']}")
    print(f"   ROIs: {info['num_rois']} ({', '.join(info['roi_names'])})")
    print(f"   Upload: Réussi ✅")
    
    print(f"\n{Colors.GREEN}{'='*80}{Colors.END}")
    print(f"{Colors.GREEN}✅ WORKFLOW COMPLET TERMINÉ!{Colors.END}")
    print(f"{Colors.GREEN}{'='*80}{Colors.END}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Workflow interrompu{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Erreur: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
