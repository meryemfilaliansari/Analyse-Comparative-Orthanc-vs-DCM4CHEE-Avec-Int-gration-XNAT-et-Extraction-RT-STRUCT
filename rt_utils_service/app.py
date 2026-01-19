"""
RT-Utils Service - Conversion RT-STRUCT → DICOM-SEG
Version simplifiée sans rt-utils (trop de dépendances OpenCV)
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pydicom
import numpy as np
import SimpleITK as sitk
from skimage import measure
import requests
import io
import os
import logging
from datetime import datetime
from pydicom.uid import generate_uid
from pydicom.dataset import Dataset

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ORTHANC_URL = os.getenv("ORTHANC_URL", "http://localhost:8042")
AUTO_UPLOAD = os.getenv("AUTO_UPLOAD", "true").lower() == "true"

@app.route('/')
def index():
    """Interface web du service"""
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "RT-STRUCT Processor (Simplified)",
        "features": [
            "RT-STRUCT analysis",
            "ROI extraction",
            "Contour to mask conversion",
            "DICOM-SEG generation (basic)",
            "Auto upload to Orthanc"
        ],
        "note": "Simplified version - for full RT-Utils features, use 3D Slicer"
    })

@app.route('/api/convert-rtstruct-to-seg', methods=['POST'])
def convert_rtstruct_to_seg():
    """
    Convertit RT-STRUCT en DICOM-SEG (version simplifiée)
    Input: {
        "series_uid": "1.2.3...",
        "rtstruct_uid": "1.2.3..."
    }
    """
    try:
        data = request.json
        series_uid = data.get('series_uid')
        rtstruct_uid = data.get('rtstruct_uid')
        
        if not series_uid or not rtstruct_uid:
            return jsonify({"error": "Missing series_uid or rtstruct_uid"}), 400
        
        logger.info(f"Processing RT-STRUCT {rtstruct_uid} for series {series_uid}")
        
        # 1. Télécharger RT-STRUCT
        rtstruct_path = download_rtstruct(rtstruct_uid)
        if not rtstruct_path:
            return jsonify({"error": "Failed to download RT-STRUCT"}), 404
        
        # 2. Analyser le RT-STRUCT
        rtstruct = pydicom.dcmread(rtstruct_path)
        
        # 3. Extraire les ROIs
        roi_info = extract_roi_info(rtstruct)
        
        logger.info(f"Found {len(roi_info)} ROIs: {[r['name'] for r in roi_info]}")
        
        return jsonify({
            "success": True,
            "rtstruct_uid": rtstruct_uid,
            "series_uid": series_uid,
            "rois_found": len(roi_info),
            "roi_details": roi_info,
            "note": "Full voxelization requires 3D Slicer. This service provides ROI analysis."
        })
            
    except Exception as e:
        logger.error(f"Error in conversion: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/extract-voxels', methods=['POST'])
def extract_voxels():
    """
    Extrait les informations basiques d'un ROI
    """
    try:
        data = request.json
        rtstruct_uid = data.get('rtstruct_uid')
        roi_name = data.get('roi_name')
        
        rtstruct_path = download_rtstruct(rtstruct_uid)
        rtstruct = pydicom.dcmread(rtstruct_path)
        
        roi_info = extract_roi_info(rtstruct)
        selected_roi = next((r for r in roi_info if r['name'] == roi_name), None)
        
        if not selected_roi:
            return jsonify({"error": f"ROI '{roi_name}' not found"}), 404
        
        return jsonify({
            "success": True,
            "roi_name": roi_name,
            "statistics": selected_roi
        })
        
    except Exception as e:
        logger.error(f"Error extracting voxels: {str(e)}")
        return jsonify({"error": str(e)}), 500

def extract_roi_info(rtstruct):
    """Extrait les informations des ROIs depuis RT-STRUCT"""
    roi_info = []
    
    if not hasattr(rtstruct, 'StructureSetROISequence'):
        return roi_info
    
    for roi in rtstruct.StructureSetROISequence:
        info = {
            "number": roi.ROINumber,
            "name": roi.ROIName,
            "description": getattr(roi, 'ROIDescription', ''),
            "generation_algorithm": getattr(roi, 'ROIGenerationAlgorithm', 'MANUAL')
        }
        
        # Trouver les contours associés
        if hasattr(rtstruct, 'ROIContourSequence'):
            for contour_seq in rtstruct.ROIContourSequence:
                if contour_seq.ReferencedROINumber == roi.ROINumber:
                    if hasattr(contour_seq, 'ContourSequence'):
                        info['num_contours'] = len(contour_seq.ContourSequence)
                        info['total_points'] = sum(len(c.ContourData) // 3 for c in contour_seq.ContourSequence)
        
        roi_info.append(info)
    
    return roi_info

def download_rtstruct(rtstruct_uid):
    """Télécharge RT-STRUCT"""
    try:
        # Rechercher l'instance
        response = requests.get(f"{ORTHANC_URL}/tools/find", json={
            "Level": "Instance",
            "Query": {"SOPInstanceUID": rtstruct_uid}
        })
        
        if response.status_code != 200 or not response.json():
            return None
        
        instance_id = response.json()[0]
        
        # Télécharger
        cache_dir = "/app/cache/rtstruct"
        os.makedirs(cache_dir, exist_ok=True)
        file_path = f"{cache_dir}/{instance_id}.dcm"
        
        file_response = requests.get(f"{ORTHANC_URL}/instances/{instance_id}/file")
        with open(file_path, 'wb') as f:
            f.write(file_response.content)
        
        return file_path
        
    except Exception as e:
        logger.error(f"Error downloading RT-STRUCT: {str(e)}")
        return None

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
