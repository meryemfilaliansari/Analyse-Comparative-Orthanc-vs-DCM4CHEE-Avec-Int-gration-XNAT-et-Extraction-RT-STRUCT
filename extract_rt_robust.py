#!/usr/bin/env python3
"""
Extraction RT-STRUCT robuste avec pydicom pur
"""
import os
import numpy as np
import pydicom
from pathlib import Path
import zipfile

def extract_rt_robust(dicom_folder, output_dir="extracted_rois_robust"):
    print(f"\n=== Extraction Robuste RT-STRUCT ===")
    print(f"Dossier: {dicom_folder}\n")
    
    # 1. Charger fichiers
    ct_slices = []
    rtstruct_ds = None
    
    for file in sorted(Path(dicom_folder).glob("*.dcm")):
        try:
            ds = pydicom.dcmread(str(file))
            if ds.Modality == "CT":
                ct_slices.append(ds)
            elif ds.Modality == "RTSTRUCT":
                rtstruct_ds = ds
        except Exception as e:
            print(f"Erreur lecture {file.name}: {e}")
    
    print(f"Trouves: {len(ct_slices)} CTs, RT-STRUCT: {'Oui' if rtstruct_ds else 'Non'}")
    
    if not rtstruct_ds:
        print("❌ Aucun RT-STRUCT")
        return False
    
    if len(ct_slices) < 10:
        print(f"❌ Insuffisant CTs ({len(ct_slices)})")
        return False
    
    # 2. Trier CTs par position Z
    ct_slices.sort(key=lambda x: float(x.ImagePositionPatient[2]))
    
    # 3. Créer volume CT
    print("\n=== Construction volume CT ===")
    rows = ct_slices[0].Rows
    cols = ct_slices[0].Columns
    num_slices = len(ct_slices)
    
    ct_volume = np.zeros((rows, cols, num_slices), dtype=np.int16)
    for i, ds in enumerate(ct_slices):
        ct_volume[:, :, i] = ds.pixel_array
    
    print(f"Volume CT: {ct_volume.shape}")
    
    # 4. Extraire ROIs
    print("\n=== Extraction ROIs ===")
    os.makedirs(output_dir, exist_ok=True)
    
    roi_count = 0
    for roi_contour in rtstruct_ds.ROIContourSequence:
        try:
            # Trouver nom ROI
            roi_number = roi_contour.ReferencedROINumber
            roi_name = "Unknown"
            for struct_roi in rtstruct_ds.StructureSetROISequence:
                if struct_roi.ROINumber == roi_number:
                    roi_name = struct_roi.ROIName
                    break
            
            print(f"\nROI: {roi_name}")
            
            # Créer masque 3D
            mask = np.zeros((rows, cols, num_slices), dtype=np.uint8)
            
            if not hasattr(roi_contour, 'ContourSequence'):
                print(f"  Pas de contours")
                continue
            
            contour_count = 0
            for contour in roi_contour.ContourSequence:
                # Obtenir points contour
                points = np.array(contour.ContourData).reshape(-1, 3)
                
                # Trouver slice correspondante
                z_pos = points[0, 2]
                slice_idx = np.argmin([abs(float(ds.ImagePositionPatient[2]) - z_pos) for ds in ct_slices])
                
                if slice_idx < num_slices:
                    # Convertir points 3D en pixels 2D
                    ds = ct_slices[slice_idx]
                    origin = np.array(ds.ImagePositionPatient) if hasattr(ds, 'ImagePositionPatient') else np.array([0, 0, 0])
                    
                    # Essayer plusieurs attributs pour spacing
                    if hasattr(ds, 'PixelSpacing'):
                        spacing = np.array([float(ds.PixelSpacing[0]), float(ds.PixelSpacing[1]), 1.0])
                    elif hasattr(ds, 'ImagerPixelSpacing'):
                        spacing = np.array([float(ds.ImagerPixelSpacing[0]), float(ds.ImagerPixelSpacing[1]), 1.0])
                    else:
                        # Valeur par défaut: 1mm x 1mm
                        spacing = np.array([1.0, 1.0, 1.0])
                    
                    pixels = []
                    for point in points:
                        # Conversion monde → pixel
                        rel = point - origin
                        px = int(rel[0] / spacing[0])
                        py = int(rel[1] / spacing[1])
                        pixels.append([py, px])  # Attention: row, col
                    
                    # Remplir polygone
                    pixels = np.array(pixels)
                    from PIL import Image, ImageDraw
                    img = Image.new('L', (cols, rows), 0)
                    draw = ImageDraw.Draw(img)
                    draw.polygon([tuple(p[::-1]) for p in pixels], outline=1, fill=1)
                    mask[:, :, slice_idx] = np.maximum(mask[:, :, slice_idx], np.array(img))
                    contour_count += 1
            
            print(f"  {contour_count} contours, {np.sum(mask)} voxels actifs")
            
            # Sauver masque
            np_file = os.path.join(output_dir, f"{roi_name}_mask.npy")
            np.save(np_file, mask)
            print(f"  ✓ {np_file}")
            
            # Sauver slices PNG
            slice_dir = os.path.join(output_dir, f"{roi_name}_slices")
            os.makedirs(slice_dir, exist_ok=True)
            
            from PIL import Image
            for i in range(num_slices):
                if np.any(mask[:, :, i]):
                    img = Image.fromarray((mask[:, :, i] * 255).astype(np.uint8))
                    img.save(os.path.join(slice_dir, f"slice_{i:03d}.png"))
            
            print(f"  ✓ Slices → {slice_dir}")
            roi_count += 1
            
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n✅ TERMINE! {roi_count} ROIs extraites dans: {output_dir}")
    return True

if __name__ == "__main__":
    import sys
    dicom_folder = r"C:\Users\awati\Desktop\pacs\rt_complete_sample"
    if len(sys.argv) > 1:
        dicom_folder = sys.argv[1]
    
    extract_rt_robust(dicom_folder)
