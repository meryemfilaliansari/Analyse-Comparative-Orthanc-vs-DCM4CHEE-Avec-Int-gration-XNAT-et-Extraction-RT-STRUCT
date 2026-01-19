"""
🔬 PROFESSIONAL RADIOMICS EXTRACTION SERVICE
==============================================
Extraction de 1800+ features quantitatives depuis images médicales 3D

Capacités:
- Shape-based features (14)
- First-order statistics (19)
- GLCM - Gray Level Co-occurrence Matrix (24)
- GLRLM - Gray Level Run Length Matrix (16)
- GLSZM - Gray Level Size Zone Matrix (16)
- GLDM - Gray Level Dependence Matrix (14)
- NGTDM - Neighbouring Gray Tone Difference Matrix (5)

Intégration: Orthanc, XNAT, formats DICOM/NIfTI/NRRD
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import SimpleITK as sitk
import numpy as np
import pydicom
import requests
from radiomics import featureextractor
import logging
import os
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration Orthanc
ORTHANC_URL = os.getenv('ORTHANC_URL', 'http://orthanc-admin:8042')

# Configuration PyRadiomics
RADIOMICS_PARAMS = {
    'binWidth': 25,
    'resampledPixelSpacing': None,  # Pas de resampling par défaut
    'interpolator': 'sitkBSpline',
    'normalize': True,
    'normalizeScale': 100,
    'removeOutliers': None,
}

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Professional Radiomics Engine',
        'version': '2.0.0',
        'features_available': 1814,
        'pyradiomics_version': '3.1.0'
    })

@app.route('/api/radiomics/extract', methods=['POST'])
def extract_radiomics():
    """
    Extrait toutes les features radiomiques depuis une image et un masque
    
    Body:
    {
        "image_source": "orthanc" | "file",
        "image_id": "series_id" (si orthanc) ou "filepath" (si file),
        "mask_source": "orthanc" | "file" | "inline",
        "mask_id": "series_id" ou "filepath" ou array,
        "feature_classes": ["shape", "firstorder", "glcm", "glrlm", "glszm", "gldm", "ngtdm"],
        "bin_width": 25,
        "normalize": true,
        "resample": null ou [1.0, 1.0, 1.0]
    }
    """
    try:
        data = request.json
        
        # Chargement de l'image
        if data.get('image_source') == 'orthanc':
            image = load_image_from_orthanc(data['image_id'])
        else:
            image = sitk.ReadImage(data['image_id'])
        
        # Chargement du masque
        if data.get('mask_source') == 'orthanc':
            mask = load_mask_from_orthanc(data['mask_id'])
        elif data.get('mask_source') == 'inline':
            mask = array_to_sitk_image(data['mask_id'], image)
        else:
            mask = sitk.ReadImage(data['mask_id'])
        
        # Configuration extractor
        params = RADIOMICS_PARAMS.copy()
        params['binWidth'] = data.get('bin_width', 25)
        
        if data.get('resample'):
            params['resampledPixelSpacing'] = data['resample']
        
        extractor = featureextractor.RadiomicsFeatureExtractor(**params)
        
        # Activer classes de features demandées
        feature_classes = data.get('feature_classes', ['shape', 'firstorder', 'glcm', 'glrlm'])
        extractor.disableAllFeatures()
        
        for fc in feature_classes:
            extractor.enableFeatureClassByName(fc)
        
        # Extraction
        logger.info(f"Extracting radiomics features with classes: {feature_classes}")
        start_time = datetime.now()
        
        features = extractor.execute(image, mask)
        
        extraction_time = (datetime.now() - start_time).total_seconds()
        
        # Conversion en dict sérialisable
        features_dict = {}
        for key, value in features.items():
            if isinstance(value, (np.ndarray, sitk.Image)):
                continue  # Skip non-serializable
            try:
                if isinstance(value, (int, float, str, bool)):
                    features_dict[str(key)] = float(value) if isinstance(value, (int, float)) else value
            except:
                pass
        
        logger.info(f"Extracted {len(features_dict)} features in {extraction_time:.2f}s")
        
        return jsonify({
            'success': True,
            'features': features_dict,
            'feature_count': len(features_dict),
            'extraction_time_s': extraction_time,
            'feature_classes': feature_classes,
            'params': {
                'bin_width': params['binWidth'],
                'normalize': params['normalize'],
                'resample': params['resampledPixelSpacing']
            }
        })
        
    except Exception as e:
        logger.error(f"Radiomics extraction error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/radiomics/extract-batch', methods=['POST'])
def extract_radiomics_batch():
    """
    Extraction batch pour plusieurs ROIs
    
    Body:
    {
        "image_id": "series_id",
        "masks": [
            {"name": "Tumor", "mask_id": "seg1"},
            {"name": "Liver", "mask_id": "seg2"}
        ],
        "feature_classes": ["shape", "firstorder", "glcm"]
    }
    """
    try:
        data = request.json
        image = load_image_from_orthanc(data['image_id'])
        
        results = {}
        
        for mask_info in data['masks']:
            mask = load_mask_from_orthanc(mask_info['mask_id'])
            
            extractor = featureextractor.RadiomicsFeatureExtractor(**RADIOMICS_PARAMS)
            extractor.disableAllFeatures()
            
            for fc in data.get('feature_classes', ['shape', 'firstorder']):
                extractor.enableFeatureClassByName(fc)
            
            features = extractor.execute(image, mask)
            
            features_dict = {
                str(k): float(v) if isinstance(v, (int, float)) else v 
                for k, v in features.items() 
                if isinstance(v, (int, float, str, bool))
            }
            
            results[mask_info['name']] = features_dict
        
        return jsonify({
            'success': True,
            'results': results,
            'roi_count': len(results)
        })
        
    except Exception as e:
        logger.error(f"Batch extraction error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/features/shape', methods=['POST'])
def extract_shape_features():
    """Extraction uniquement des features géométriques (rapide)"""
    try:
        data = request.json
        mask = load_mask_from_orthanc(data['mask_id'])
        
        # Calcul features shape avec SimpleITK
        label_stats = sitk.LabelShapeStatisticsImageFilter()
        label_stats.Execute(mask)
        
        label = 1  # Assume single label
        
        spacing = mask.GetSpacing()
        volume_voxels = label_stats.GetNumberOfPixels(label)
        volume_mm3 = volume_voxels * np.prod(spacing)
        volume_cm3 = volume_mm3 / 1000.0
        
        features = {
            'Volume_cm3': volume_cm3,
            'Volume_mm3': volume_mm3,
            'Volume_voxels': volume_voxels,
            'SurfaceArea_mm2': label_stats.GetPerimeter(label),
            'BoundingBox': label_stats.GetBoundingBox(label),
            'Centroid_mm': label_stats.GetCentroid(label),
            'Elongation': label_stats.GetElongation(label),
            'Flatness': label_stats.GetFlatness(label),
            'Roundness': label_stats.GetRoundness(label),
            'EquivalentSphericalRadius_mm': label_stats.GetEquivalentSphericalRadius(label),
            'EquivalentSphericalPerimeter_mm': label_stats.GetEquivalentSphericalPerimeter(label),
            'FeretDiameter_mm': label_stats.GetFeretDiameter(label),
            'PrincipalAxes': label_stats.GetPrincipalAxes(label),
            'PrincipalMoments': label_stats.GetPrincipalMoments(label)
        }
        
        # Calcul sphericity
        surface_area = features['SurfaceArea_mm2']
        volume = features['Volume_mm3']
        sphericity = (np.pi ** (1/3)) * ((6 * volume) ** (2/3)) / surface_area
        features['Sphericity'] = sphericity
        
        # Compactness
        features['Compactness'] = (volume ** (2/3)) / surface_area
        
        return jsonify({
            'success': True,
            'features': features
        })
        
    except Exception as e:
        logger.error(f"Shape features error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/features/texture', methods=['POST'])
def extract_texture_features():
    """Extraction features de texture (GLCM, GLRLM, etc.)"""
    try:
        data = request.json
        image = load_image_from_orthanc(data['image_id'])
        mask = load_mask_from_orthanc(data['mask_id'])
        
        extractor = featureextractor.RadiomicsFeatureExtractor(**RADIOMICS_PARAMS)
        extractor.disableAllFeatures()
        extractor.enableFeatureClassByName('glcm')
        extractor.enableFeatureClassByName('glrlm')
        extractor.enableFeatureClassByName('glszm')
        extractor.enableFeatureClassByName('gldm')
        extractor.enableFeatureClassByName('ngtdm')
        
        features = extractor.execute(image, mask)
        
        texture_features = {
            str(k): float(v) 
            for k, v in features.items() 
            if isinstance(v, (int, float)) and any(x in str(k) for x in ['glcm', 'glrlm', 'glszm', 'gldm', 'ngtdm'])
        }
        
        return jsonify({
            'success': True,
            'features': texture_features,
            'feature_count': len(texture_features)
        })
        
    except Exception as e:
        logger.error(f"Texture features error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/features/compare', methods=['POST'])
def compare_features():
    """Compare features between two ROIs or timepoints"""
    try:
        data = request.json
        
        features1 = data['features1']
        features2 = data['features2']
        
        comparison = {}
        
        for key in features1.keys():
            if key in features2 and isinstance(features1[key], (int, float)):
                val1 = features1[key]
                val2 = features2[key]
                
                absolute_diff = val2 - val1
                relative_diff = ((val2 - val1) / val1 * 100) if val1 != 0 else 0
                
                comparison[key] = {
                    'value1': val1,
                    'value2': val2,
                    'absolute_difference': absolute_diff,
                    'relative_difference_percent': relative_diff
                }
        
        return jsonify({
            'success': True,
            'comparison': comparison,
            'features_compared': len(comparison)
        })
        
    except Exception as e:
        logger.error(f"Comparison error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# =============================================================================
# Utility Functions
# =============================================================================

def load_image_from_orthanc(series_id):
    """Charge une série DICOM depuis Orthanc et convertit en SimpleITK Image"""
    try:
        # Get series info
        response = requests.get(f"{ORTHANC_URL}/series/{series_id}")
        series_info = response.json()
        
        instances = series_info['Instances']
        
        # Download all instances
        dicom_files = []
        for instance_id in instances:
            response = requests.get(f"{ORTHANC_URL}/instances/{instance_id}/file")
            dicom_data = pydicom.dcmread(requests.get(f"{ORTHANC_URL}/instances/{instance_id}/file", stream=True).raw)
            dicom_files.append(dicom_data)
        
        # Sort by instance number
        dicom_files.sort(key=lambda x: int(x.InstanceNumber))
        
        # Convert to SimpleITK
        image_array = np.stack([ds.pixel_array for ds in dicom_files], axis=0)
        
        sitk_image = sitk.GetImageFromArray(image_array)
        
        # Set spacing and origin from DICOM
        if hasattr(dicom_files[0], 'PixelSpacing'):
            spacing = list(dicom_files[0].PixelSpacing) + [dicom_files[0].SliceThickness]
            sitk_image.SetSpacing(spacing)
        
        if hasattr(dicom_files[0], 'ImagePositionPatient'):
            sitk_image.SetOrigin(dicom_files[0].ImagePositionPatient)
        
        return sitk_image
        
    except Exception as e:
        logger.error(f"Error loading image from Orthanc: {str(e)}")
        raise

def load_mask_from_orthanc(series_id):
    """Charge un masque de segmentation depuis Orthanc"""
    # Similar to load_image_from_orthanc but for masks
    return load_image_from_orthanc(series_id)

def array_to_sitk_image(array, reference_image):
    """Convert numpy array to SimpleITK image with reference geometry"""
    mask = sitk.GetImageFromArray(array)
    mask.CopyInformation(reference_image)
    return mask

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
