#!/usr/bin/env python3
"""
Analyse complète des ROIs extraites
"""
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import json

def analyze_rois(roi_dir="extracted_rois_robust"):
    """
    Analyse volumétrique et statistique des ROIs
    """
    print("\n" + "="*60)
    print("ANALYSE ROIS RT-STRUCT")
    print("="*60)
    
    roi_dir = Path(roi_dir)
    results = {}
    
    # Trouver tous les masques
    mask_files = list(roi_dir.glob("*_mask.npy"))
    
    if not mask_files:
        print("❌ Aucun masque trouvé")
        return
    
    print(f"\n📊 {len(mask_files)} ROIs trouvées\n")
    
    for mask_file in sorted(mask_files):
        roi_name = mask_file.stem.replace("_mask", "")
        print(f"\n{'='*50}")
        print(f"ROI: {roi_name}")
        print(f"{'='*50}")
        
        # Charger masque
        mask = np.load(mask_file)
        print(f"Dimensions: {mask.shape} (Rows × Cols × Slices)")
        
        # Statistiques volumétriques
        total_voxels = np.sum(mask)
        print(f"Voxels actifs: {total_voxels:,}")
        
        # Volume (en supposant spacing 1×1×1 mm)
        volume_mm3 = total_voxels * 1.0 * 1.0 * 1.0
        volume_cm3 = volume_mm3 / 1000
        volume_ml = volume_cm3
        print(f"Volume estimé: {volume_cm3:.2f} cm³ ({volume_ml:.2f} mL)")
        
        # Distribution par slice
        slices_with_roi = []
        voxels_per_slice = []
        
        for i in range(mask.shape[2]):
            count = np.sum(mask[:, :, i])
            if count > 0:
                slices_with_roi.append(i)
                voxels_per_slice.append(count)
        
        print(f"Slices actives: {len(slices_with_roi)}/{mask.shape[2]}")
        print(f"  Première slice: {min(slices_with_roi)}")
        print(f"  Dernière slice: {max(slices_with_roi)}")
        print(f"  Étendue: {max(slices_with_roi) - min(slices_with_roi) + 1} slices")
        
        if voxels_per_slice:
            print(f"Voxels par slice:")
            print(f"  Min: {min(voxels_per_slice):,}")
            print(f"  Max: {max(voxels_per_slice):,}")
            print(f"  Moyenne: {np.mean(voxels_per_slice):,.0f}")
        
        # Centroid
        coords = np.where(mask > 0)
        centroid = [np.mean(coords[0]), np.mean(coords[1]), np.mean(coords[2])]
        print(f"Centroid (pixels): ({centroid[0]:.1f}, {centroid[1]:.1f}, {centroid[2]:.1f})")
        
        # Bounding box
        bbox = {
            'row_min': int(np.min(coords[0])),
            'row_max': int(np.max(coords[0])),
            'col_min': int(np.min(coords[1])),
            'col_max': int(np.max(coords[1])),
            'slice_min': int(np.min(coords[2])),
            'slice_max': int(np.max(coords[2]))
        }
        bbox_size = [
            bbox['row_max'] - bbox['row_min'] + 1,
            bbox['col_max'] - bbox['col_min'] + 1,
            bbox['slice_max'] - bbox['slice_min'] + 1
        ]
        print(f"Bounding Box: {bbox_size[0]}×{bbox_size[1]}×{bbox_size[2]} pixels")
        
        # Sauver résultats
        results[roi_name] = {
            'shape': mask.shape,
            'total_voxels': int(total_voxels),
            'volume_cm3': round(volume_cm3, 2),
            'volume_ml': round(volume_ml, 2),
            'slices_active': len(slices_with_roi),
            'slice_range': [int(min(slices_with_roi)), int(max(slices_with_roi))],
            'centroid': [round(c, 2) for c in centroid],
            'bbox': bbox,
            'bbox_size': bbox_size
        }
    
    # Sauver rapport JSON
    json_file = roi_dir / "analysis_report.json"
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n\n{'='*60}")
    print(f"✅ Rapport sauvegardé: {json_file}")
    print(f"{'='*60}\n")
    
    # Créer visualisations
    create_visualizations(roi_dir, results)
    
    return results

def create_visualizations(roi_dir, results):
    """
    Créer graphiques de visualisation
    """
    print("\n📈 Création visualisations...")
    
    # 1. Comparaison volumes
    plt.figure(figsize=(10, 6))
    names = list(results.keys())
    volumes = [results[name]['volume_cm3'] for name in names]
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    
    bars = plt.bar(names, volumes, color=colors[:len(names)])
    plt.ylabel('Volume (cm³)', fontsize=12)
    plt.title('Comparaison Volumes ROIs', fontsize=14, fontweight='bold')
    plt.grid(axis='y', alpha=0.3)
    
    # Ajouter valeurs sur barres
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f} cm³',
                ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(roi_dir / 'volumes_comparison.png', dpi=150, bbox_inches='tight')
    print(f"  ✓ {roi_dir / 'volumes_comparison.png'}")
    plt.close()
    
    # 2. Distribution par slice pour chaque ROI
    mask_files = list(roi_dir.glob("*_mask.npy"))
    
    fig, axes = plt.subplots(len(mask_files), 1, figsize=(12, 4*len(mask_files)))
    if len(mask_files) == 1:
        axes = [axes]
    
    for idx, mask_file in enumerate(sorted(mask_files)):
        roi_name = mask_file.stem.replace("_mask", "")
        mask = np.load(mask_file)
        
        voxels_per_slice = [np.sum(mask[:, :, i]) for i in range(mask.shape[2])]
        
        axes[idx].plot(voxels_per_slice, linewidth=2, color=colors[idx % len(colors)])
        axes[idx].fill_between(range(len(voxels_per_slice)), voxels_per_slice, alpha=0.3, color=colors[idx % len(colors)])
        axes[idx].set_title(f'{roi_name} - Distribution par Slice', fontsize=12, fontweight='bold')
        axes[idx].set_xlabel('Slice Index', fontsize=10)
        axes[idx].set_ylabel('Voxels', fontsize=10)
        axes[idx].grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(roi_dir / 'slice_distribution.png', dpi=150, bbox_inches='tight')
    print(f"  ✓ {roi_dir / 'slice_distribution.png'}")
    plt.close()
    
    # 3. Vue centrale de chaque ROI
    fig, axes = plt.subplots(1, len(mask_files), figsize=(6*len(mask_files), 6))
    if len(mask_files) == 1:
        axes = [axes]
    
    for idx, mask_file in enumerate(sorted(mask_files)):
        roi_name = mask_file.stem.replace("_mask", "")
        mask = np.load(mask_file)
        
        # Trouver slice avec le plus de voxels
        voxels_per_slice = [np.sum(mask[:, :, i]) for i in range(mask.shape[2])]
        max_slice = np.argmax(voxels_per_slice)
        
        axes[idx].imshow(mask[:, :, max_slice], cmap='hot', interpolation='nearest')
        axes[idx].set_title(f'{roi_name}\nSlice {max_slice} ({voxels_per_slice[max_slice]:,} voxels)', 
                           fontsize=12, fontweight='bold')
        axes[idx].axis('off')
    
    plt.tight_layout()
    plt.savefig(roi_dir / 'rois_preview.png', dpi=150, bbox_inches='tight')
    print(f"  ✓ {roi_dir / 'rois_preview.png'}")
    plt.close()
    
    print("\n✅ Visualisations créées!")

if __name__ == "__main__":
    import sys
    roi_dir = "extracted_rois_robust"
    if len(sys.argv) > 1:
        roi_dir = sys.argv[1]
    
    analyze_rois(roi_dir)
