============================================================
3D SLICER - IMPORT ROIs RT-STRUCT
============================================================


Heart:
  File: Heart.nii.gz
  Volume: 105.0 cm³
  Voxels: 105,000
  Color (RGB): (255, 165, 0)

Lung_Left:
  File: Lung_Left.nii.gz
  Volume: 241.27 cm³
  Voxels: 241,273
  Color (RGB): (0, 255, 255)

Tumor:
  File: Tumor.nii.gz
  Volume: 31.54 cm³
  Voxels: 31,537
  Color (RGB): (255, 0, 0)

============================================================
WORKFLOW CONSEILLE:
============================================================

1. Charger CT:
   File → Add Data → [CT files]
   Cela crée le volume de référence

2. Ajouter ROIs comme segmentation:
   File → Add Data → [Tumor.nii.gz, Heart.nii.gz, ...]
   Modules → Segmentations → Importer comme segmentation

3. Visualiser ensemble:
   - Vue 3D montre CT + segmentations
   - Vues 2D (Axial/Sagittal/Coronal) avec superposition

4. Calculs supplémentaires:
   Modules → Segmentation Statistics → Analyser volumes
   Modules → Segmentation → Boolean operations (intersection, union)
