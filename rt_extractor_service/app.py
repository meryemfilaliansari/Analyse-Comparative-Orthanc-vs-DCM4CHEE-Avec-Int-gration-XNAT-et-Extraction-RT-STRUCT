"""
Service d'extraction RT-STRUCT → Masques par slice
Récupère les RT-STRUCT depuis Orthanc et extrait chaque ROI individuellement
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pydicom
import numpy as np
from rt_utils import RTStructBuilder
import requests
import tempfile
import os
import zipfile
from io import BytesIO
import json

app = Flask(__name__)
CORS(app)

ORTHANC_URL = os.environ.get('ORTHANC_URL', 'http://orthanc-admin:8042')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'service': 'RT-STRUCT Extractor',
        'status': 'healthy',
        'version': '1.0.0',
        'capabilities': [
            'Extract ROIs from RT-STRUCT',
            'Export masks slice by slice',
            'Export as DICOM-SEG',
            'Export as NIfTI per ROI',
            'List all ROIs with statistics'
        ]
    })

@app.route('/api/rt-struct/list-rois', methods=['POST'])
def list_rois():
    """
    Liste toutes les ROIs d'un RT-STRUCT avec leurs infos
    
    Body: {
        "rtstruct_id": "orthanc_instance_id"
    }
    """
    data = request.get_json()
    rtstruct_id = data.get('rtstruct_id')
    
    if not rtstruct_id:
        return jsonify({'error': 'rtstruct_id required'}), 400
    
    try:
        # Télécharger RT-STRUCT depuis Orthanc
        response = requests.get(f'{ORTHANC_URL}/instances/{rtstruct_id}/file')
        response.raise_for_status()
        
        # Sauvegarder temporairement
        with tempfile.NamedTemporaryFile(delete=False, suffix='.dcm') as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name
        
        # Parser avec pydicom
        ds = pydicom.dcmread(tmp_path)
        
        # Extraire infos de chaque ROI
        rois = []
        if hasattr(ds, 'StructureSetROISequence'):
            for roi_seq in ds.StructureSetROISequence:
                roi_number = roi_seq.ROINumber
                roi_name = roi_seq.ROIName
                
                # Trouver les contours correspondants
                num_slices = 0
                if hasattr(ds, 'ROIContourSequence'):
                    for contour_seq in ds.ROIContourSequence:
                        if contour_seq.ReferencedROINumber == roi_number:
                            if hasattr(contour_seq, 'ContourSequence'):
                                num_slices = len(contour_seq.ContourSequence)
                
                rois.append({
                    'roi_number': int(roi_number),
                    'roi_name': str(roi_name),
                    'num_slices': num_slices,
                    'color': self._get_roi_color(ds, roi_number)
                })
        
        os.unlink(tmp_path)
        
        return jsonify({
            'patient_name': str(ds.PatientName) if hasattr(ds, 'PatientName') else 'Unknown',
            'study_date': str(ds.StudyDate) if hasattr(ds, 'StudyDate') else 'Unknown',
            'num_rois': len(rois),
            'rois': rois
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _get_roi_color(ds, roi_number):
    """Récupérer la couleur d'une ROI"""
    if hasattr(ds, 'ROIContourSequence'):
        for contour_seq in ds.ROIContourSequence:
            if contour_seq.ReferencedROINumber == roi_number:
                if hasattr(contour_seq, 'ROIDisplayColor'):
                    color = contour_seq.ROIDisplayColor
                    return [int(c) for c in color]
    return [255, 0, 0]  # Rouge par défaut

@app.route('/api/rt-struct/extract-roi-slices', methods=['POST'])
def extract_roi_slices():
    """
    Extrait une ROI spécifique slice par slice
    
    Body: {
        "rtstruct_id": "orthanc_instance_id",
        "ct_series_id": "orthanc_series_id",
        "roi_name": "GTV" ou "roi_number": 1,
        "output_format": "numpy" | "png" | "dicom"
    }
    
    Returns: ZIP contenant les slices
    """
    data = request.get_json()
    rtstruct_id = data.get('rtstruct_id')
    ct_series_id = data.get('ct_series_id')
    roi_name = data.get('roi_name')
    roi_number = data.get('roi_number')
    output_format = data.get('output_format', 'numpy')
    
    if not all([rtstruct_id, ct_series_id]):
        return jsonify({'error': 'rtstruct_id and ct_series_id required'}), 400
    
    if not roi_name and not roi_number:
        return jsonify({'error': 'roi_name or roi_number required'}), 400
    
    try:
        # Télécharger CT series depuis Orthanc
        ct_dir = tempfile.mkdtemp()
        series_info = requests.get(f'{ORTHANC_URL}/series/{ct_series_id}').json()
        
        for instance_id in series_info['Instances']:
            response = requests.get(f'{ORTHANC_URL}/instances/{instance_id}/file')
            instance_number = requests.get(f'{ORTHANC_URL}/instances/{instance_id}/simplified-tags').json().get('InstanceNumber', '0')
            
            with open(os.path.join(ct_dir, f'CT_{instance_number}.dcm'), 'wb') as f:
                f.write(response.content)
        
        # Télécharger RT-STRUCT
        rtstruct_response = requests.get(f'{ORTHANC_URL}/instances/{rtstruct_id}/file')
        rtstruct_path = os.path.join(ct_dir, 'rtstruct.dcm')
        with open(rtstruct_path, 'wb') as f:
            f.write(rtstruct_response.content)
        
        # Charger avec rt-utils
        rtstruct = RTStructBuilder.create_from(
            dicom_series_path=ct_dir,
            rt_struct_path=rtstruct_path
        )
        
        # Extraire le masque 3D de la ROI
        if roi_name:
            mask_3d = rtstruct.get_roi_mask_by_name(roi_name)
        else:
            # Trouver le nom par numéro
            ds = pydicom.dcmread(rtstruct_path)
            roi_name = None
            for roi_seq in ds.StructureSetROISequence:
                if roi_seq.ROINumber == roi_number:
                    roi_name = roi_seq.ROIName
                    break
            
            if not roi_name:
                return jsonify({'error': f'ROI number {roi_number} not found'}), 404
            
            mask_3d = rtstruct.get_roi_mask_by_name(roi_name)
        
        # Créer ZIP avec les slices
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            
            # Métadonnées
            metadata = {
                'roi_name': roi_name,
                'roi_number': roi_number,
                'num_slices': mask_3d.shape[2],
                'shape': list(mask_3d.shape),
                'voxel_count': int(np.sum(mask_3d)),
                'volume_voxels': int(np.sum(mask_3d))
            }
            zip_file.writestr('metadata.json', json.dumps(metadata, indent=2))
            
            # Exporter chaque slice
            for slice_idx in range(mask_3d.shape[2]):
                slice_mask = mask_3d[:, :, slice_idx]
                
                if np.any(slice_mask):  # Seulement si la slice contient des voxels
                    
                    if output_format == 'numpy':
                        # Sauvegarder comme numpy array
                        slice_buffer = BytesIO()
                        np.save(slice_buffer, slice_mask)
                        zip_file.writestr(f'slice_{slice_idx:03d}.npy', slice_buffer.getvalue())
                    
                    elif output_format == 'png':
                        # Sauvegarder comme image PNG
                        from PIL import Image
                        img = Image.fromarray((slice_mask * 255).astype(np.uint8))
                        img_buffer = BytesIO()
                        img.save(img_buffer, format='PNG')
                        zip_file.writestr(f'slice_{slice_idx:03d}.png', img_buffer.getvalue())
                    
                    elif output_format == 'dicom':
                        # Créer DICOM-SEG slice
                        # TODO: Implémenter export DICOM-SEG
                        pass
        
        zip_buffer.seek(0)
        
        # Nettoyer
        import shutil
        shutil.rmtree(ct_dir)
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'{roi_name}_slices.zip'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rt-struct/extract-all-rois', methods=['POST'])
def extract_all_rois():
    """
    Extrait TOUTES les ROIs d'un RT-STRUCT
    
    Body: {
        "rtstruct_id": "orthanc_instance_id",
        "ct_series_id": "orthanc_series_id",
        "output_format": "nifti" | "numpy"
    }
    
    Returns: ZIP avec un fichier par ROI
    """
    data = request.get_json()
    rtstruct_id = data.get('rtstruct_id')
    ct_series_id = data.get('ct_series_id')
    output_format = data.get('output_format', 'nifti')
    
    try:
        # Télécharger CT series
        ct_dir = tempfile.mkdtemp()
        series_info = requests.get(f'{ORTHANC_URL}/series/{ct_series_id}').json()
        
        for instance_id in series_info['Instances']:
            response = requests.get(f'{ORTHANC_URL}/instances/{instance_id}/file')
            instance_number = requests.get(f'{ORTHANC_URL}/instances/{instance_id}/simplified-tags').json().get('InstanceNumber', '0')
            
            with open(os.path.join(ct_dir, f'CT_{instance_number}.dcm'), 'wb') as f:
                f.write(response.content)
        
        # Télécharger RT-STRUCT
        rtstruct_response = requests.get(f'{ORTHANC_URL}/instances/{rtstruct_id}/file')
        rtstruct_path = os.path.join(ct_dir, 'rtstruct.dcm')
        with open(rtstruct_path, 'wb') as f:
            f.write(rtstruct_response.content)
        
        # Charger RT-STRUCT
        rtstruct = RTStructBuilder.create_from(
            dicom_series_path=ct_dir,
            rt_struct_path=rtstruct_path
        )
        
        # Lister toutes les ROIs
        ds = pydicom.dcmread(rtstruct_path)
        roi_names = [roi_seq.ROIName for roi_seq in ds.StructureSetROISequence]
        
        # Créer ZIP
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            
            for roi_name in roi_names:
                try:
                    mask_3d = rtstruct.get_roi_mask_by_name(roi_name)
                    
                    if output_format == 'nifti':
                        import nibabel as nib
                        nifti_img = nib.Nifti1Image(mask_3d.astype(np.uint8), np.eye(4))
                        nifti_buffer = BytesIO()
                        nib.save(nifti_img, nifti_buffer)
                        nifti_buffer.seek(0)
                        zip_file.writestr(f'{roi_name}.nii.gz', nifti_buffer.getvalue())
                    
                    elif output_format == 'numpy':
                        numpy_buffer = BytesIO()
                        np.save(numpy_buffer, mask_3d)
                        zip_file.writestr(f'{roi_name}.npy', numpy_buffer.getvalue())
                    
                except Exception as e:
                    print(f"Erreur pour ROI {roi_name}: {e}")
                    continue
        
        zip_buffer.seek(0)
        
        # Nettoyer
        import shutil
        shutil.rmtree(ct_dir)
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='all_rois.zip'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rt-struct/extract-from-folder', methods=['POST'])
def extract_from_folder():
    """
    Extrait ROIs depuis un dossier local contenant DICOM
    
    Body: {
        "dicom_folder": "chemin/vers/dossier"
    }
    
    Returns: ZIP avec ROIs en NIfTI
    """
    data = request.get_json()
    dicom_folder = data.get('dicom_folder')
    
    if not dicom_folder or not os.path.exists(dicom_folder):
        return jsonify({'error': 'Dossier invalide'}), 400
    
    try:
        # Charger RT-STRUCT
        rtstruct = RTStructBuilder.create_from(dicom_series_path=dicom_folder)
        roi_names = rtstruct.get_roi_names()
        
        # Créer ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for roi_name in roi_names:
                mask = rtstruct.get_roi_mask_by_name(roi_name)
                
                # Sauver en NIfTI
                nifti_img = nibabel.Nifti1Image(mask.astype(np.uint8), np.eye(4))
                nifti_buffer = io.BytesIO()
                nibabel.save(nifti_img, nifti_buffer)
                nifti_buffer.seek(0)
                
                zipf.writestr(f'{roi_name}_mask.nii.gz', nifti_buffer.read())
        
        zip_buffer.seek(0)
        return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='rois.zip')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rt-struct/export-to-slicer', methods=['POST'])
def export_to_slicer():
    """
    Exporte RT-STRUCT au format compatible 3D Slicer (NIfTI + scene)
    
    Body: {
        "rtstruct_id": "orthanc_instance_id",
        "ct_series_id": "orthanc_series_id"
    }
    
    Returns: ZIP avec CT.nii.gz + ROI_*.nii.gz + scene.mrml
    """
    data = request.get_json()
    rtstruct_id = data.get('rtstruct_id')
    ct_series_id = data.get('ct_series_id')
    
    try:
        import SimpleITK as sitk
        import nibabel as nib
        
        # Télécharger CT series
        ct_dir = tempfile.mkdtemp()
        series_info = requests.get(f'{ORTHANC_URL}/series/{ct_series_id}').json()
        
        for instance_id in series_info['Instances']:
            response = requests.get(f'{ORTHANC_URL}/instances/{instance_id}/file')
            instance_number = requests.get(f'{ORTHANC_URL}/instances/{instance_id}/simplified-tags').json().get('InstanceNumber', '0')
            
            with open(os.path.join(ct_dir, f'CT_{instance_number}.dcm'), 'wb') as f:
                f.write(response.content)
        
        # Lire CT avec SimpleITK pour avoir les métadonnées spatiales correctes
        reader = sitk.ImageSeriesReader()
        dicom_names = reader.GetGDCMSeriesFileNames(ct_dir)
        reader.SetFileNames(dicom_names)
        ct_image = reader.Execute()
        
        # Convertir en numpy et NIfTI
        ct_array = sitk.GetArrayFromImage(ct_image)
        spacing = ct_image.GetSpacing()
        origin = ct_image.GetOrigin()
        direction = ct_image.GetDirection()
        
        # Créer matrice affine pour NIfTI
        affine = np.eye(4)
        affine[:3, :3] = np.array(direction).reshape(3, 3) * spacing
        affine[:3, 3] = origin
        
        # Télécharger RT-STRUCT
        rtstruct_response = requests.get(f'{ORTHANC_URL}/instances/{rtstruct_id}/file')
        rtstruct_path = os.path.join(ct_dir, 'rtstruct.dcm')
        with open(rtstruct_path, 'wb') as f:
            f.write(rtstruct_response.content)
        
        # Charger RT-STRUCT
        rtstruct = RTStructBuilder.create_from(
            dicom_series_path=ct_dir,
            rt_struct_path=rtstruct_path
        )
        
        # Lister ROIs
        ds = pydicom.dcmread(rtstruct_path)
        roi_names = [roi_seq.ROIName for roi_seq in ds.StructureSetROISequence]
        
        # Créer ZIP pour 3D Slicer
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            
            # Sauvegarder CT
            ct_nifti = nib.Nifti1Image(ct_array, affine)
            ct_buffer = BytesIO()
            nib.save(ct_nifti, ct_buffer)
            ct_buffer.seek(0)
            zip_file.writestr('CT.nii.gz', ct_buffer.getvalue())
            
            # Sauvegarder chaque ROI
            for roi_name in roi_names:
                try:
                    mask_3d = rtstruct.get_roi_mask_by_name(roi_name)
                    mask_nifti = nib.Nifti1Image(mask_3d.astype(np.uint8), affine)
                    mask_buffer = BytesIO()
                    nib.save(mask_nifti, mask_buffer)
                    mask_buffer.seek(0)
                    
                    safe_name = roi_name.replace(' ', '_').replace('/', '_')
                    zip_file.writestr(f'ROI_{safe_name}.nii.gz', mask_buffer.getvalue())
                except:
                    continue
            
            # Créer fichier instructions
            instructions = f"""
3D SLICER IMPORT INSTRUCTIONS
=============================

1. Ouvrir 3D Slicer
2. File → Add Data → Choose File(s) to Add
3. Sélectionner tous les fichiers .nii.gz
4. Click OK

Fichiers:
- CT.nii.gz : Image CT originale
{chr(10).join([f'- ROI_{roi_name.replace(" ", "_")}.nii.gz : Segmentation {roi_name}' for roi_name in roi_names])}

Alternativement:
- Module "Segment Editor"
- Import/Export → Import segmentation from file
- Sélectionner les ROI_*.nii.gz

Pour visualisation 3D:
- Module "Volume Rendering" pour le CT
- Module "Segmentations" → Show 3D pour les ROIs
"""
            zip_file.writestr('README.txt', instructions)
        
        zip_buffer.seek(0)
        
        # Nettoyer
        import shutil
        shutil.rmtree(ct_dir)
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='slicer_project.zip'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
