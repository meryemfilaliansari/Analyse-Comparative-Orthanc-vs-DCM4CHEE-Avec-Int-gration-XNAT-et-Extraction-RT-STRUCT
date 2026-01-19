#!/usr/bin/env python3
"""
Conversion masques → NIfTI pour 3D Slicer
"""
import numpy as np
import nibabel as nib
from pathlib import Path
import json

def create_nifti_from_masks(roi_dir="extracted_rois_robust", output_dir="slicer_ready"):
    """
    Convertit les masques NumPy en NIfTI avec métadonnées
    """
    print("\n" + "="*60)
    print("CONVERSION VERS 3D SLICER")
    print("="*60)
    
    roi_dir = Path(roi_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    mask_files = list(roi_dir.glob("*_mask.npy"))
    
    if not mask_files:
        print("❌ Aucun masque trouvé")
        return
    
    print(f"\n🔄 Conversion de {len(mask_files)} ROIs...\n")
    
    # Définir affine matrix (identité pour spacing 1×1×1 mm)
    affine = np.eye(4)
    affine[0, 3] = 0    # Origin X
    affine[1, 3] = 0    # Origin Y
    affine[2, 3] = 0    # Origin Z
    
    # Couleurs pour chaque ROI (RGB pour segmentation)
    colors = {
        'Tumor': (255, 0, 0),      # Red
        'Heart': (255, 165, 0),    # Orange
        'Lung_Left': (0, 255, 255) # Cyan
    }
    
    roi_info = {}
    
    for mask_file in sorted(mask_files):
        roi_name = mask_file.stem.replace("_mask", "")
        
        print(f"📦 {roi_name}")
        
        # Charger masque
        mask = np.load(mask_file)
        
        # Créer image NIfTI
        # Important: NIfTI utilise convention (z, y, x) = (slice, row, col)
        nifti_img = nib.Nifti1Image(
            mask.astype(np.uint8),  # Convertir en uint8 (0-255)
            affine
        )
        
        # Ajouter métadonnées
        nifti_img.header.set_data_dtype(np.uint8)
        
        # Sauver
        output_file = output_dir / f"{roi_name}.nii.gz"
        nib.save(nifti_img, output_file)
        print(f"  ✓ {output_file}")
        
        # Statistiques
        volume_voxels = np.sum(mask)
        volume_cm3 = volume_voxels * 1.0 * 1.0 * 1.0 / 1000
        
        roi_info[roi_name] = {
            'nifti_file': str(output_file.name),
            'volume_cm3': round(volume_cm3, 2),
            'color_rgb': colors.get(roi_name, (128, 128, 128)),
            'shape': list(mask.shape),
            'voxels': int(volume_voxels)
        }
    
    # Créer fichier instructions
    print("\n📝 Création guide d'import...")
    
    instructions = {
        'application': '3D Slicer',
        'version': '5.0+',
        'instructions': [
            "1. Ouvrir 3D Slicer",
            "2. File → Add Data → Sélectionner le fichier CT (.nii.gz ou DICOM)",
            "3. Pour chaque ROI:",
            "   - File → Add Data → Sélectionner le fichier ROI (.nii.gz)",
            "   - Dans 'Data' module: Drag & drop vers la branche du CT",
            "   - Ou: Modules → Segmentations → Import → Importer comme segmentation",
            "4. Utiliser 'Segmentations' module pour:",
            "   - Éditer les ROIs",
            "   - Calculer volumes",
            "   - Export DICOM-SEG"
        ],
        'rois': roi_info
    }
    
    # Sauver JSON
    json_file = output_dir / "slicer_guide.json"
    with open(json_file, 'w') as f:
        json.dump(instructions, f, indent=2)
    
    print(f"  ✓ {json_file}")
    
    # Créer README
    readme = output_dir / "README_SLICER.txt"
    with open(readme, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("3D SLICER - IMPORT ROIs RT-STRUCT\n")
        f.write("="*60 + "\n\n")
        
        for roi_name, info in roi_info.items():
            f.write(f"\n{roi_name}:\n")
            f.write(f"  File: {info['nifti_file']}\n")
            f.write(f"  Volume: {info['volume_cm3']} cm³\n")
            f.write(f"  Voxels: {info['voxels']:,}\n")
            f.write(f"  Color (RGB): {info['color_rgb']}\n")
        
        f.write("\n" + "="*60 + "\n")
        f.write("WORKFLOW CONSEILLE:\n")
        f.write("="*60 + "\n\n")
        f.write("1. Charger CT:\n")
        f.write("   File → Add Data → [CT files]\n")
        f.write("   Cela crée le volume de référence\n\n")
        
        f.write("2. Ajouter ROIs comme segmentation:\n")
        f.write("   File → Add Data → [Tumor.nii.gz, Heart.nii.gz, ...]\n")
        f.write("   Modules → Segmentations → Importer comme segmentation\n\n")
        
        f.write("3. Visualiser ensemble:\n")
        f.write("   - Vue 3D montre CT + segmentations\n")
        f.write("   - Vues 2D (Axial/Sagittal/Coronal) avec superposition\n\n")
        
        f.write("4. Calculs supplémentaires:\n")
        f.write("   Modules → Segmentation Statistics → Analyser volumes\n")
        f.write("   Modules → Segmentation → Boolean operations (intersection, union)\n")
    
    print(f"  ✓ {readme}")
    
    print(f"\n{'='*60}")
    print(f"✅ PRET POUR 3D SLICER!")
    print(f"Dossier: {output_dir}")
    print(f"{'='*60}\n")
    
    # Lister fichiers
    print("Fichiers generés:")
    for f in sorted(output_dir.glob("*")):
        print(f"  - {f.name}")

if __name__ == "__main__":
    import sys
    roi_dir = "extracted_rois_robust"
    output_dir = "slicer_ready"
    
    if len(sys.argv) > 1:
        roi_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    create_nifti_from_masks(roi_dir, output_dir)
