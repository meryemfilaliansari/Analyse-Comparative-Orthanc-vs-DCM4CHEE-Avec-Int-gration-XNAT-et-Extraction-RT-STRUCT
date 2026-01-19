#!/usr/bin/env python3
"""
🎨 Visualiseur Direct de RT-STRUCT
==================================
Affiche les contours de votre RT-STRUCT Prostate-AEC-023
"""

import requests
import pydicom
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from pathlib import Path

ORTHANC_URL = "http://localhost:8042"

print("="*80)
print("🎨 VISUALISEUR RT-STRUCT - Prostate-AEC-023")
print("="*80)

# Vérifier si le fichier existe déjà
rtstruct_path = Path("rt_diagnostic_output/rtstruct.dcm")

if not rtstruct_path.exists():
    print("\n❌ Fichier RT-STRUCT non trouvé!")
    print("   Exécutez d'abord: python diagnostic_rt_direct.py")
    exit(1)

print(f"\n✅ Chargement: {rtstruct_path}")

# Charger le RT-STRUCT
ds = pydicom.dcmread(str(rtstruct_path))

print(f"\n📋 Patient: {ds.PatientName}")
print(f"📅 Date: {ds.StudyDate}")

# Extraire les ROIs
rois = {}
if hasattr(ds, 'StructureSetROISequence'):
    for roi in ds.StructureSetROISequence:
        rois[roi.ROINumber] = {
            'name': roi.ROIName,
            'number': roi.ROINumber
        }

print(f"\n🎯 {len(rois)} ROIs trouvés:")
for roi_num, roi_info in rois.items():
    print(f"   {roi_num}. {roi_info['name']}")

# Extraire les contours organisés par slice Z
print("\n📐 Extraction des contours...")

contours_by_roi = {}

if hasattr(ds, 'ROIContourSequence'):
    for contour_seq in ds.ROIContourSequence:
        roi_num = contour_seq.ReferencedROINumber
        roi_name = rois[roi_num]['name']
        
        contours_by_roi[roi_name] = {}
        
        if hasattr(contour_seq, 'ContourSequence'):
            for contour in contour_seq.ContourSequence:
                if hasattr(contour, 'ContourData'):
                    points = np.array(contour.ContourData).reshape(-1, 3)
                    z = points[0, 2]  # Position Z du contour
                    
                    if z not in contours_by_roi[roi_name]:
                        contours_by_roi[roi_name][z] = []
                    
                    contours_by_roi[roi_name][z].append(points[:, :2])  # Garder seulement X,Y

print("✅ Contours extraits!\n")

# Afficher les statistiques
for roi_name, contours in contours_by_roi.items():
    num_slices = len(contours)
    total_points = sum(len(c[0]) for c in contours.values())
    print(f"   • {roi_name}: {num_slices} tranches, {total_points} points")

# Visualisation
print("\n🎨 Création de la visualisation...")

# Trouver toutes les positions Z uniques
all_z = set()
for roi_contours in contours_by_roi.values():
    all_z.update(roi_contours.keys())
all_z = sorted(list(all_z))

print(f"   Tranches disponibles: {len(all_z)}")

# Choisir quelques tranches représentatives
num_display = min(6, len(all_z))
step = max(1, len(all_z) // num_display)
selected_z = all_z[::step][:num_display]

print(f"   Affichage de {len(selected_z)} tranches")

# Créer la figure
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
fig.suptitle(f'RT-STRUCT: {ds.PatientName} - {ds.StudyDate}', fontsize=16, fontweight='bold')
axes = axes.flatten()

# Couleurs pour chaque ROI
colors = {
    'Rectum': 'brown',
    'Prostate': 'red',
    'Bladder': 'blue',
    'Femur_Head_L': 'green',
    'Femur_Head_R': 'orange'
}

# Dessiner chaque tranche
for idx, z_pos in enumerate(selected_z):
    if idx >= len(axes):
        break
    
    ax = axes[idx]
    ax.set_title(f'Tranche Z={z_pos:.1f} mm', fontweight='bold')
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    
    # Dessiner les contours de chaque ROI pour cette tranche
    for roi_name, roi_contours in contours_by_roi.items():
        if z_pos in roi_contours:
            color = colors.get(roi_name, 'gray')
            
            for contour_points in roi_contours[z_pos]:
                # Dessiner le contour
                ax.plot(contour_points[:, 0], contour_points[:, 1], 
                       color=color, linewidth=2, label=roi_name)
                
                # Remplir le contour (semi-transparent)
                polygon = Polygon(contour_points, alpha=0.3, 
                                facecolor=color, edgecolor=color, linewidth=2)
                ax.add_patch(polygon)
    
    # Légende (sans doublons)
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='upper right', fontsize=8)

# Cacher les axes non utilisés
for idx in range(len(selected_z), len(axes)):
    axes[idx].axis('off')

plt.tight_layout()

# Sauvegarder
output_path = "rt_diagnostic_output/rtstruct_visualization.png"
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"\n✅ Visualisation sauvegardée: {output_path}")

print("\n" + "="*80)
print("🎨 AFFICHAGE DE LA VISUALISATION")
print("="*80)

plt.show()

print("\n✅ Terminé!")
print("\n📂 Fichiers générés:")
print(f"   • {output_path}")
print(f"   • rt_diagnostic_output/rtstruct.dcm")
print(f"   • rt_diagnostic_output/metadata.json")

print("\n" + "="*80)
