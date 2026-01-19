"""
DICOMweb Server with RT STRUCT and Segmentation Support
Provides advanced tools for:
- RT STRUCT creation and manipulation
- DICOM segmentation
- Pixel/voxel manipulation
- Slice extraction and masking
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pydicom
import numpy as np
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import generate_uid
import requests
import io
import logging
from datetime import datetime

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ORTHANC_URL = "http://orthanc-admin:8042"

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "features": [
        "RT STRUCT creation",
        "Segmentation",
        "Pixel manipulation",
        "Voxel extraction",
        "Slice masking"
    ]})

@app.route('/api/studies/<study_id>/create-rtstruct', methods=['POST'])
def create_rtstruct(study_id):
    """
    Create RT STRUCT from segmentation masks
    """
    try:
        data = request.json
        contours = data.get('contours', [])
        
        # Fetch study from Orthanc
        study_url = f"{ORTHANC_URL}/studies/{study_id}"
        response = requests.get(study_url)
        if response.status_code != 200:
            return jsonify({"error": "Study not found"}), 404
        
        study = response.json()
        
        # Create RT STRUCT dataset
        rt_struct = create_rt_struct_dataset(study, contours)
        
        # Save and upload to Orthanc
        dicom_file = io.BytesIO()
        rt_struct.save_as(dicom_file, write_like_original=False)
        dicom_file.seek(0)
        
        # Upload to Orthanc
        upload_response = requests.post(
            f"{ORTHANC_URL}/instances",
            files={'file': dicom_file},
            headers={'Content-Type': 'application/dicom'}
        )
        
        if upload_response.status_code == 200:
            return jsonify({
                "success": True,
                "instance_id": upload_response.json()['ID']
            })
        else:
            return jsonify({"error": "Failed to upload RT STRUCT"}), 500
            
    except Exception as e:
        logger.error(f"Error creating RT STRUCT: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/instances/<instance_id>/segment', methods=['POST'])
def segment_instance(instance_id):
    """
    Create segmentation masks from DICOM instance
    """
    try:
        data = request.json
        threshold = data.get('threshold', 128)
        
        # Fetch instance from Orthanc
        instance_url = f"{ORTHANC_URL}/instances/{instance_id}/file"
        response = requests.get(instance_url)
        if response.status_code != 200:
            return jsonify({"error": "Instance not found"}), 404
        
        # Load DICOM
        dicom_data = pydicom.dcmread(io.BytesIO(response.content))
        
        # Extract pixels
        pixels = dicom_data.pixel_array
        
        # Create binary mask
        mask = (pixels > threshold).astype(np.uint8)
        
        # Find contours (simplified)
        contours = extract_contours(mask)
        
        return jsonify({
            "success": True,
            "mask_shape": mask.shape,
            "contours_count": len(contours),
            "contours": contours
        })
        
    except Exception as e:
        logger.error(f"Error segmenting instance: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/instances/<instance_id>/extract-voxels', methods=['POST'])
def extract_voxels(instance_id):
    """
    Extract voxel data from DICOM instance
    """
    try:
        data = request.json
        roi = data.get('roi', None)  # Region of interest [x, y, z, width, height, depth]
        
        # Fetch instance from Orthanc
        instance_url = f"{ORTHANC_URL}/instances/{instance_id}/file"
        response = requests.get(instance_url)
        if response.status_code != 200:
            return jsonify({"error": "Instance not found"}), 404
        
        # Load DICOM
        dicom_data = pydicom.dcmread(io.BytesIO(response.content))
        pixels = dicom_data.pixel_array
        
        # Extract ROI if specified
        if roi:
            x, y, width, height = roi['x'], roi['y'], roi['width'], roi['height']
            voxels = pixels[y:y+height, x:x+width]
        else:
            voxels = pixels
        
        # Calculate statistics
        stats = {
            "mean": float(np.mean(voxels)),
            "std": float(np.std(voxels)),
            "min": float(np.min(voxels)),
            "max": float(np.max(voxels)),
            "shape": voxels.shape
        }
        
        return jsonify({
            "success": True,
            "statistics": stats,
            "voxel_data": voxels.tolist() if voxels.size < 10000 else "Too large to return"
        })
        
    except Exception as e:
        logger.error(f"Error extracting voxels: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/instances/<instance_id>/create-mask', methods=['POST'])
def create_slice_mask(instance_id):
    """
    Create custom mask for slice separation
    """
    try:
        data = request.json
        mask_type = data.get('type', 'threshold')  # threshold, region, custom
        params = data.get('params', {})
        
        # Fetch instance
        instance_url = f"{ORTHANC_URL}/instances/{instance_id}/file"
        response = requests.get(instance_url)
        if response.status_code != 200:
            return jsonify({"error": "Instance not found"}), 404
        
        dicom_data = pydicom.dcmread(io.BytesIO(response.content))
        pixels = dicom_data.pixel_array
        
        # Create mask based on type
        if mask_type == 'threshold':
            threshold = params.get('threshold', 128)
            mask = (pixels > threshold).astype(np.uint8) * 255
        elif mask_type == 'region':
            mask = create_region_mask(pixels, params)
        else:
            mask = np.zeros_like(pixels)
        
        # Create new DICOM with mask
        masked_instance = create_masked_dicom(dicom_data, mask)
        
        # Save and upload
        dicom_file = io.BytesIO()
        masked_instance.save_as(dicom_file, write_like_original=False)
        dicom_file.seek(0)
        
        upload_response = requests.post(
            f"{ORTHANC_URL}/instances",
            files={'file': dicom_file},
            headers={'Content-Type': 'application/dicom'}
        )
        
        if upload_response.status_code == 200:
            return jsonify({
                "success": True,
                "masked_instance_id": upload_response.json()['ID']
            })
        else:
            return jsonify({"error": "Failed to upload masked instance"}), 500
            
    except Exception as e:
        logger.error(f"Error creating mask: {str(e)}")
        return jsonify({"error": str(e)}), 500

def create_rt_struct_dataset(study, contours):
    """Create RT STRUCT DICOM dataset"""
    rt_struct = Dataset()
    
    # SOP Common Module
    rt_struct.SOPClassUID = '1.2.840.10008.5.1.4.1.1.481.3'  # RT Structure Set Storage
    rt_struct.SOPInstanceUID = generate_uid()
    
    # Patient Module
    rt_struct.PatientName = study.get('PatientMainDicomTags', {}).get('PatientName', 'Anonymous')
    rt_struct.PatientID = study.get('PatientMainDicomTags', {}).get('PatientID', 'Unknown')
    
    # General Study Module
    rt_struct.StudyInstanceUID = study.get('MainDicomTags', {}).get('StudyInstanceUID', generate_uid())
    rt_struct.StudyDate = datetime.now().strftime('%Y%m%d')
    rt_struct.StudyTime = datetime.now().strftime('%H%M%S')
    
    # RT Series Module
    rt_struct.Modality = 'RTSTRUCT'
    rt_struct.SeriesInstanceUID = generate_uid()
    rt_struct.SeriesNumber = '999'
    
    # Structure Set Module
    rt_struct.StructureSetLabel = 'AI Segmentation'
    rt_struct.StructureSetDate = datetime.now().strftime('%Y%m%d')
    rt_struct.StructureSetTime = datetime.now().strftime('%H%M%S')
    
    return rt_struct

def extract_contours(mask):
    """Extract contours from binary mask"""
    from skimage import measure
    
    contours_list = []
    contours = measure.find_contours(mask, 0.5)
    
    for contour in contours[:10]:  # Limit to 10 contours
        contours_list.append({
            "points": contour.tolist(),
            "length": len(contour)
        })
    
    return contours_list

def create_region_mask(pixels, params):
    """Create mask for specific region"""
    mask = np.zeros_like(pixels)
    x, y, width, height = params.get('x', 0), params.get('y', 0), params.get('width', 100), params.get('height', 100)
    mask[y:y+height, x:x+width] = 255
    return mask

def create_masked_dicom(original_dicom, mask):
    """Create new DICOM with applied mask"""
    masked_dicom = original_dicom.copy()
    masked_dicom.SOPInstanceUID = generate_uid()
    masked_dicom.SeriesDescription = f"{original_dicom.get('SeriesDescription', 'Unknown')} - Masked"
    
    # Apply mask to pixels
    original_pixels = original_dicom.pixel_array
    masked_pixels = np.where(mask > 0, original_pixels, 0)
    masked_dicom.PixelData = masked_pixels.tobytes()
    
    return masked_dicom

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
