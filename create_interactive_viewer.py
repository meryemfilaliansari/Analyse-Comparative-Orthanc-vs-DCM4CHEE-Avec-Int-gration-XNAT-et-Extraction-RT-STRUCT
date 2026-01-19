#!/usr/bin/env python3
"""
🌐 Visualiseur Web Interactif RT-STRUCT
========================================
Interface web avec slider pour naviguer les tranches
"""

import requests
import pydicom
import numpy as np
import json
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ORTHANC_URL = "http://localhost:8042"

print("="*80)
print("🌐 CRÉATION DU VISUALISEUR WEB INTERACTIF")
print("="*80)

# Charger le RT-STRUCT
rtstruct_path = Path("rt_diagnostic_output/rtstruct.dcm")

if not rtstruct_path.exists():
    print("\n❌ Fichier RT-STRUCT non trouvé!")
    print("   Exécutez: python diagnostic_rt_direct.py")
    exit(1)

print(f"\n✅ Chargement: {rtstruct_path}")
ds = pydicom.dcmread(str(rtstruct_path))

# Extraire les ROIs
rois = {}
if hasattr(ds, 'StructureSetROISequence'):
    for roi in ds.StructureSetROISequence:
        rois[roi.ROINumber] = roi.ROIName

print(f"📋 Patient: {ds.PatientName}")
print(f"🎯 {len(rois)} ROIs: {', '.join(rois.values())}")

# Extraire les contours par ROI et par Z
contours_by_roi = {}

if hasattr(ds, 'ROIContourSequence'):
    for contour_seq in ds.ROIContourSequence:
        roi_num = contour_seq.ReferencedROINumber
        roi_name = rois[roi_num]
        
        contours_by_roi[roi_name] = {}
        
        if hasattr(contour_seq, 'ContourSequence'):
            for contour in contour_seq.ContourSequence:
                if hasattr(contour, 'ContourData'):
                    points = np.array(contour.ContourData).reshape(-1, 3)
                    z = round(points[0, 2], 1)
                    
                    if z not in contours_by_roi[roi_name]:
                        contours_by_roi[roi_name][z] = []
                    
                    contours_by_roi[roi_name][z].append(points)

# Toutes les positions Z
all_z = set()
for roi_contours in contours_by_roi.values():
    all_z.update(roi_contours.keys())
all_z = sorted(list(all_z))

print(f"📐 {len(all_z)} tranches de Z={min(all_z):.1f} à Z={max(all_z):.1f} mm")

# Couleurs
colors = {
    'Rectum': 'brown',
    'Prostate': 'red',
    'Bladder': 'blue',
    'Femur_Head_L': 'green',
    'Femur_Head_R': 'orange'
}

# Créer une figure interactive avec Plotly
print("\n🎨 Création de l'interface web interactive...")

# Créer les frames pour l'animation/slider
frames = []

for z_pos in all_z:
    frame_data = []
    
    for roi_name, roi_contours in contours_by_roi.items():
        if z_pos in roi_contours:
            color = colors.get(roi_name, 'gray')
            
            for contour_points in roi_contours[z_pos]:
                # Fermer le contour
                x = np.append(contour_points[:, 0], contour_points[0, 0])
                y = np.append(contour_points[:, 1], contour_points[0, 1])
                
                frame_data.append(
                    go.Scatter(
                        x=x, y=y,
                        mode='lines',
                        line=dict(color=color, width=3),
                        fill='toself',
                        fillcolor=color,
                        opacity=0.4,
                        name=roi_name,
                        showlegend=True,
                        legendgroup=roi_name
                    )
                )
    
    frames.append(go.Frame(data=frame_data, name=f'{z_pos:.1f}'))

# Créer la figure initiale (première tranche)
initial_z = all_z[len(all_z)//2]  # Tranche du milieu
initial_data = []

for roi_name, roi_contours in contours_by_roi.items():
    if initial_z in roi_contours:
        color = colors.get(roi_name, 'gray')
        
        for contour_points in roi_contours[initial_z]:
            x = np.append(contour_points[:, 0], contour_points[0, 0])
            y = np.append(contour_points[:, 1], contour_points[0, 1])
            
            initial_data.append(
                go.Scatter(
                    x=x, y=y,
                    mode='lines',
                    line=dict(color=color, width=3),
                    fill='toself',
                    fillcolor=color,
                    opacity=0.4,
                    name=roi_name,
                    showlegend=True,
                    legendgroup=roi_name
                )
            )

# Créer la figure
fig = go.Figure(data=initial_data, frames=frames)

# Ajouter le slider
sliders = [dict(
    active=len(all_z)//2,
    yanchor="top",
    y=0,
    xanchor="left",
    x=0.1,
    currentvalue=dict(
        prefix="Position Z: ",
        suffix=" mm",
        visible=True,
        xanchor="right"
    ),
    steps=[
        dict(
            args=[[f.name], dict(
                frame=dict(duration=0, redraw=True),
                mode="immediate",
                transition=dict(duration=0)
            )],
            label=f'{z:.1f}',
            method="animate"
        ) for z, f in zip(all_z, frames)
    ]
)]

# Boutons de contrôle
updatemenus = [dict(
    type="buttons",
    direction="left",
    x=0.1,
    xanchor="left",
    y=1.15,
    yanchor="top",
    buttons=[
        dict(label="▶ Play",
             method="animate",
             args=[None, dict(frame=dict(duration=200, redraw=True),
                            fromcurrent=True,
                            mode='immediate',
                            transition=dict(duration=0))]),
        dict(label="⏸ Pause",
             method="animate",
             args=[[None], dict(frame=dict(duration=0, redraw=False),
                                mode="immediate",
                                transition=dict(duration=0))])
    ]
)]

# Mise en page
fig.update_layout(
    title=dict(
        text=f'RT-STRUCT: {ds.PatientName} - {ds.StudyDate}<br>' +
             f'<sub>Utilisez le slider pour naviguer entre les {len(all_z)} tranches</sub>',
        x=0.5,
        xanchor='center'
    ),
    xaxis=dict(title="X (mm)", constrain='domain'),
    yaxis=dict(title="Y (mm)", scaleanchor="x", scaleratio=1),
    sliders=sliders,
    updatemenus=updatemenus,
    hovermode='closest',
    width=1200,
    height=800,
    showlegend=True,
    legend=dict(
        x=1.01,
        y=1,
        xanchor='left',
        yanchor='top'
    )
)

# Sauvegarder
output_html = "rt_diagnostic_output/rtstruct_interactive.html"
fig.write_html(output_html)

print(f"\n✅ Interface web créée: {output_html}")
print("\n" + "="*80)
print("🌐 OUVERTURE DE L'INTERFACE WEB")
print("="*80)
print("\nFonctionnalités:")
print("  ✅ Slider pour naviguer les 41 tranches")
print("  ✅ Boutons Play/Pause pour animation automatique")
print("  ✅ Légende interactive (cliquez pour masquer/afficher)")
print("  ✅ Zoom, pan, export image")
print("  ✅ Fonctionne 100% dans le navigateur (pas besoin de Python)")
print("\n" + "="*80)

# Ouvrir dans le navigateur
import webbrowser
webbrowser.open(f'file:///{Path(output_html).absolute()}')

print(f"\n✅ Interface ouverte dans votre navigateur!")
print(f"\n📂 Fichier: {Path(output_html).absolute()}")
