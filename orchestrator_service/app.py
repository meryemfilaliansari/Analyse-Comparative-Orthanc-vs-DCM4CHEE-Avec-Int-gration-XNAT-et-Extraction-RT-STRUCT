"""
RT Workflow Orchestrator
Détecte les RT-STRUCT et orchestre le pipeline complet
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import logging
import json
import os

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ORTHANC_URL = os.getenv("ORTHANC_URL", "http://localhost:8042")
RT_UTILS_URL = os.getenv("RT_UTILS_URL", "http://rt-utils-processor:5000")
ITK_VTK_URL = os.getenv("ITK_VTK_URL", "http://itk-vtk-processor:5000")
AUTO_PROCESS = os.getenv("AUTO_PROCESS", "true").lower() == "true"

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "RT Workflow Orchestrator",
        "auto_process": AUTO_PROCESS,
        "endpoints": {
            "orthanc": ORTHANC_URL,
            "rt_utils": RT_UTILS_URL,
            "itk_vtk": ITK_VTK_URL
        }
    })

@app.route('/webhook/orthanc/stable-study', methods=['POST'])
def orthanc_webhook():
    """
    Webhook appelé par Orthanc quand une étude devient stable
    """
    try:
        data = request.json
        study_id = data.get('ID')
        
        logger.info(f"Received webhook for study: {study_id}")
        
        # Vérifier si l'étude contient un RT-STRUCT
        study_info = requests.get(f"{ORTHANC_URL}/studies/{study_id}").json()
        
        has_rtstruct = False
        rtstruct_instance = None
        ct_series = None
        
        for series_id in study_info['Series']:
            series_info = requests.get(f"{ORTHANC_URL}/series/{series_id}").json()
            modality = series_info['MainDicomTags'].get('Modality')
            
            if modality == 'RTSTRUCT':
                has_rtstruct = True
                instances = series_info['Instances']
                if instances:
                    rtstruct_instance = instances[0]
            elif modality == 'CT':
                ct_series = series_id
        
        if has_rtstruct and ct_series and AUTO_PROCESS:
            logger.info(f"Found RT-STRUCT, triggering automatic processing")
            
            # Obtenir les UIDs
            ct_series_info = requests.get(f"{ORTHANC_URL}/series/{ct_series}").json()
            ct_series_uid = ct_series_info['MainDicomTags']['SeriesInstanceUID']
            
            rtstruct_info = requests.get(f"{ORTHANC_URL}/instances/{rtstruct_instance}").json()
            rtstruct_uid = rtstruct_info['MainDicomTags']['SOPInstanceUID']
            
            # Lancer le workflow
            result = trigger_rt_workflow(ct_series_uid, rtstruct_uid)
            
            return jsonify({
                "success": True,
                "workflow_triggered": True,
                "result": result
            })
        
        return jsonify({
            "success": True,
            "workflow_triggered": False,
            "has_rtstruct": has_rtstruct
        })
        
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/trigger-workflow', methods=['POST'])
def trigger_workflow_manual():
    """
    Déclenche manuellement le workflow
    """
    try:
        data = request.json
        series_uid = data.get('series_uid')
        rtstruct_uid = data.get('rtstruct_uid')
        
        result = trigger_rt_workflow(series_uid, rtstruct_uid)
        
        return jsonify({
            "success": True,
            "result": result
        })
        
    except Exception as e:
        logger.error(f"Error triggering workflow: {str(e)}")
        return jsonify({"error": str(e)}), 500

def trigger_rt_workflow(ct_series_uid, rtstruct_uid):
    """
    Workflow complet:
    1. RT-Utils: RT-STRUCT → DICOM-SEG
    2. ITK/VTK: Post-processing (optionnel)
    3. Upload vers Orthanc
    """
    workflow_result = {
        "steps": []
    }
    
    try:
        # Étape 1: Conversion RT-STRUCT → DICOM-SEG
        logger.info("Step 1: RT-STRUCT → DICOM-SEG conversion")
        
        conversion_response = requests.post(
            f"{RT_UTILS_URL}/api/convert-rtstruct-to-seg",
            json={
                "series_uid": ct_series_uid,
                "rtstruct_uid": rtstruct_uid
            },
            timeout=300
        )
        
        if conversion_response.status_code == 200:
            conversion_result = conversion_response.json()
            workflow_result['steps'].append({
                "step": "rt_utils_conversion",
                "status": "success",
                "data": conversion_result
            })
            
            logger.info(f"Conversion successful: {conversion_result}")
        else:
            workflow_result['steps'].append({
                "step": "rt_utils_conversion",
                "status": "failed",
                "error": conversion_response.text
            })
            return workflow_result
        
        # Étape 2: Post-processing ITK/VTK (optionnel)
        # Pour l'instant, on skip
        
        return workflow_result
        
    except Exception as e:
        logger.error(f"Error in workflow: {str(e)}")
        workflow_result['error'] = str(e)
        return workflow_result

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
