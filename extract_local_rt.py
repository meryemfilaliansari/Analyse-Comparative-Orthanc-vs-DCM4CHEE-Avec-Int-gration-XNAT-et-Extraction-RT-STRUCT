#!/usr/bin/env python3
"""
Extraction locale RT-STRUCT depuis dossier DICOM
"""
import os
import sys
import pydicom
import numpy as np
from rt_utils import RTStructBuilder
import SimpleITK as sitk
import zipfile
from pathlib import Path

def extract_rt_from_folder(dicom_folder, output_dir="extracted_rois"):
    """
    Extrait les ROIs d'un RT-STRUCT avec CTs locaux
    """
    print(f"\n=== Analyse dossier: {dicom_folder} ===")
    
    # 1. Trouver les fichiers
    ct_files = []
    rtstruct_file = None
    
    for file in Path(dicom_folder).glob("*.dcm"):
        try:
            ds = pydicom.dcmread(str(file), stop_before_pixels=True)
            if ds.Modality == "CT":
                ct_files.append(str(file))
            elif ds.Modality == "RTSTRUCT":
                rtstruct_file = str(file)
        except Exception as e:
            continue
    
    print(f"Trouves: {len(ct_files)} CTs, RT-STRUCT: {'Oui' if rtstruct_file else 'Non'}")
    
    if not rtstruct_file:
        print("❌ Aucun RT-STRUCT trouve")
        return False
    
    if len(ct_files) < 10:
        print(f"❌ Pas assez de CTs ({len(ct_files)})")
        return False
    
    # 2. Trier les CTs par position
    ct_files.sort()
    
    # 3. Charger RT-STRUCT
    print("\n=== Chargement RT-STRUCT ===")
    rtstruct = RTStructBuilder.create_from(
        dicom_series_path=dicom_folder,
        rt_struct_path=rtstruct_file
    )
    
    # 4. Lister ROIs
    roi_names = rtstruct.get_roi_names()
    print(f"ROIs trouvees: {len(roi_names)}")
    for name in roi_names:
        print(f"  - {name}")
    
    # 5. Creer dossier sortie
    os.makedirs(output_dir, exist_ok=True)
    
    # 6. Extraire chaque ROI
    print("\n=== Extraction ===")
    for roi_name in roi_names:
        print(f"\nExtraction: {roi_name}")
        try:
            # Get mask 3D
            mask = rtstruct.get_roi_mask_by_name(roi_name)
            print(f"  Shape: {mask.shape}")
            print(f"  Voxels actifs: {np.sum(mask)}")
            
            # Sauver en NumPy
            np_file = os.path.join(output_dir, f"{roi_name}_mask.npy")
            np.save(np_file, mask)
            print(f"  ✓ {np_file}")
            
            # Sauver slices en PNG
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            slice_dir = os.path.join(output_dir, f"{roi_name}_slices")
            os.makedirs(slice_dir, exist_ok=True)
            
            for i in range(mask.shape[2]):
                if np.any(mask[:, :, i]):
                    plt.figure(figsize=(8, 8))
                    plt.imshow(mask[:, :, i], cmap='gray')
                    plt.title(f"{roi_name} - Slice {i}")
                    plt.axis('off')
                    png_file = os.path.join(slice_dir, f"slice_{i:03d}.png")
                    plt.savefig(png_file, bbox_inches='tight', dpi=100)
                    plt.close()
            
            print(f"  ✓ Slices → {slice_dir}")
            
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
    
    print(f"\n✅ TERMINE! Resultats dans: {output_dir}")
    print(f"\nContenu:")
    for item in os.listdir(output_dir):
        print(f"  - {item}")
    
    return True

if __name__ == "__main__":
    dicom_folder = r"C:\Users\awati\Desktop\pacs\rt_complete_sample"
    
    if len(sys.argv) > 1:
        dicom_folder = sys.argv[1]
    
    success = extract_rt_from_folder(dicom_folder)
    sys.exit(0 if success else 1)
