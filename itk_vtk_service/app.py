"""
ITK/VTK Service - Post-processing avancé
Morphologie, interpolation, mesures géométriques, radiomics
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import SimpleITK as sitk
import numpy as np
from scipy import ndimage
from skimage import morphology, measure
import logging

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "ITK/VTK Processor",
        "features": [
            "Morphological operations",
            "Sub-voxel interpolation",
            "Surface extraction",
            "Volume calculations",
            "Radiomics features"
        ]
    })

@app.route('/api/morphology', methods=['POST'])
def morphological_operations():
    """
    Opérations morphologiques sur masques
    """
    try:
        data = request.json
        mask_data = np.array(data.get('mask'))
        operation = data.get('operation', 'closing')
        kernel_size = data.get('kernel_size', 3)
        
        kernel = morphology.ball(kernel_size)
        
        if operation == 'closing':
            result = morphology.closing(mask_data, kernel)
        elif operation == 'opening':
            result = morphology.opening(mask_data, kernel)
        elif operation == 'dilation':
            result = morphology.dilation(mask_data, kernel)
        elif operation == 'erosion':
            result = morphology.erosion(mask_data, kernel)
        else:
            return jsonify({"error": "Unknown operation"}), 400
        
        return jsonify({
            "success": True,
            "result_shape": result.shape,
            "voxels_before": int(np.sum(mask_data)),
            "voxels_after": int(np.sum(result))
        })
        
    except Exception as e:
        logger.error(f"Error in morphology: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/interpolate', methods=['POST'])
def interpolate_mask():
    """
    Interpolation sub-voxel
    """
    try:
        data = request.json
        mask_data = np.array(data.get('mask'))
        factor = data.get('factor', 2)
        
        # SimpleITK interpolation
        image = sitk.GetImageFromArray(mask_data.astype(np.float32))
        new_size = [int(s * factor) for s in image.GetSize()]
        
        resampled = sitk.Resample(
            image,
            new_size,
            sitk.Transform(),
            sitk.sitkLinear,
            image.GetOrigin(),
            [s / factor for s in image.GetSpacing()],
            image.GetDirection(),
            0.0,
            image.GetPixelID()
        )
        
        result = sitk.GetArrayFromImage(resampled)
        
        return jsonify({
            "success": True,
            "original_shape": mask_data.shape,
            "interpolated_shape": result.shape,
            "factor": factor
        })
        
    except Exception as e:
        logger.error(f"Error in interpolation: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/extract-surface', methods=['POST'])
def extract_surface():
    """
    Extraction de surface avec marching cubes
    """
    try:
        data = request.json
        mask_data = np.array(data.get('mask'))
        spacing = data.get('spacing', [1.0, 1.0, 1.0])
        
        # Marching cubes
        verts, faces, normals, values = measure.marching_cubes(
            mask_data,
            level=0.5,
            spacing=spacing
        )
        
        # Calcul de surface
        surface_area = measure.mesh_surface_area(verts, faces)
        
        return jsonify({
            "success": True,
            "vertices": len(verts),
            "faces": len(faces),
            "surface_area_mm2": float(surface_area),
            "export_formats": ["STL", "OBJ", "VTK"]
        })
        
    except Exception as e:
        logger.error(f"Error extracting surface: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/radiomics', methods=['POST'])
def calculate_radiomics():
    """
    Calcul de features radiomiques
    """
    try:
        data = request.json
        mask_data = np.array(data.get('mask'))
        intensity_data = np.array(data.get('intensity')) if 'intensity' in data else None
        
        features = {}
        
        # Shape features
        features['volume'] = int(np.sum(mask_data))
        features['surface_area'] = calculate_surface_area(mask_data)
        features['compactness'] = calculate_compactness(mask_data)
        features['sphericity'] = calculate_sphericity(mask_data)
        
        # Intensity features (si CT disponible)
        if intensity_data is not None:
            roi_intensities = intensity_data[mask_data > 0]
            features['mean_intensity'] = float(np.mean(roi_intensities))
            features['std_intensity'] = float(np.std(roi_intensities))
            features['min_intensity'] = float(np.min(roi_intensities))
            features['max_intensity'] = float(np.max(roi_intensities))
        
        return jsonify({
            "success": True,
            "features": features
        })
        
    except Exception as e:
        logger.error(f"Error calculating radiomics: {str(e)}")
        return jsonify({"error": str(e)}), 500

def calculate_surface_area(mask):
    """Calcul approximatif de surface"""
    # Gradient pour détecter les bords
    grad = np.gradient(mask.astype(float))
    surface = np.sum(np.sqrt(grad[0]**2 + grad[1]**2 + grad[2]**2) > 0.5)
    return float(surface)

def calculate_compactness(mask):
    """Compacité = 36π * V² / S³"""
    volume = np.sum(mask)
    surface = calculate_surface_area(mask)
    if surface == 0:
        return 0.0
    return float(36 * np.pi * volume**2 / surface**3)

def calculate_sphericity(mask):
    """Sphéricité"""
    volume = np.sum(mask)
    surface = calculate_surface_area(mask)
    if surface == 0:
        return 0.0
    radius = (3 * volume / (4 * np.pi)) ** (1/3)
    ideal_surface = 4 * np.pi * radius**2
    return float(ideal_surface / surface) if surface > 0 else 0.0

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
