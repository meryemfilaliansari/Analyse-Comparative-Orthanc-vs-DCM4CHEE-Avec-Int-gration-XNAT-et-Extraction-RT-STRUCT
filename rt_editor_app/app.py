from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import requests
import os
import json
from io import BytesIO

app = Flask(__name__, 
            static_folder='.',
            template_folder='.')
CORS(app)

# Configuration
ORTHANC_URL = os.getenv('ORTHANC_URL', 'http://orthanc-admin:8042')
RT_UTILS_URL = os.getenv('RT_UTILS_URL', 'http://rt-utils-processor:5000')
ITK_VTK_URL = os.getenv('ITK_VTK_URL', 'http://itk-vtk-processor:5000')
ORCHESTRATOR_URL = os.getenv('ORCHESTRATOR_URL', 'http://rt-workflow-orchestrator:5000')

@app.route('/')
def index():
    """Serve the main RT-STRUCT Editor application"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'RT-STRUCT Editor Pro',
        'version': '1.0.0'
    })

# ============================================================================
# Orthanc Proxy Endpoints
# ============================================================================

@app.route('/api/orthanc/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def orthanc_proxy(path):
    """Proxy requests to Orthanc"""
    try:
        url = f"{ORTHANC_URL}/{path}"
        
        if request.method == 'GET':
            response = requests.get(url, params=request.args)
        elif request.method == 'POST':
            response = requests.post(url, 
                                    data=request.data,
                                    headers={'Content-Type': request.content_type})
        elif request.method == 'PUT':
            response = requests.put(url, 
                                   data=request.data,
                                   headers={'Content-Type': request.content_type})
        elif request.method == 'DELETE':
            response = requests.delete(url)
        
        return response.content, response.status_code, {'Content-Type': response.headers.get('Content-Type', 'application/json')}
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/studies', methods=['GET'])
def get_studies():
    """Get all studies from Orthanc"""
    try:
        response = requests.get(f"{ORTHANC_URL}/studies")
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/studies/<study_id>', methods=['GET'])
def get_study(study_id):
    """Get study details"""
    try:
        response = requests.get(f"{ORTHANC_URL}/studies/{study_id}")
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/series/<series_id>', methods=['GET'])
def get_series(series_id):
    """Get series details"""
    try:
        response = requests.get(f"{ORTHANC_URL}/series/{series_id}")
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# Upload Endpoints
# ============================================================================

@app.route('/api/upload', methods=['POST'])
def upload_dicom():
    """Upload DICOM file to Orthanc"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Upload to Orthanc
        response = requests.post(
            f"{ORTHANC_URL}/instances",
            files={'file': (file.filename, file.read(), 'application/dicom')}
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'orthanc_response': response.json()
            })
        else:
            return jsonify({
                'error': 'Orthanc upload failed',
                'status': response.status_code
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# RT Processing Endpoints
# ============================================================================

@app.route('/api/rt/extract-rois', methods=['POST'])
def extract_rois():
    """Extract ROIs from RT-STRUCT"""
    try:
        data = request.json
        rtstruct_uid = data.get('rtstruct_uid')
        
        if not rtstruct_uid:
            return jsonify({'error': 'rtstruct_uid required'}), 400
        
        # Call RT-Utils service
        response = requests.post(
            f"{RT_UTILS_URL}/api/extract-voxels",
            json={'rtstruct_uid': rtstruct_uid}
        )
        
        return jsonify(response.json()), response.status_code
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rt/convert-to-seg', methods=['POST'])
def convert_to_seg():
    """Convert RT-STRUCT to DICOM-SEG"""
    try:
        data = request.json
        
        # Call RT-Utils service
        response = requests.post(
            f"{RT_UTILS_URL}/api/convert-rtstruct-to-seg",
            json=data
        )
        
        return jsonify(response.json()), response.status_code
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflow/process', methods=['POST'])
def process_workflow():
    """Trigger full RT workflow"""
    try:
        data = request.json
        study_id = data.get('study_id')
        
        if not study_id:
            return jsonify({'error': 'study_id required'}), 400
        
        # Call Orchestrator
        response = requests.post(
            f"{ORCHESTRATOR_URL}/webhook/orthanc/stable-study",
            json={
                'ID': study_id,
                'Type': 'StableStudy',
                'manual_trigger': True
            }
        )
        
        return jsonify(response.json()), response.status_code
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ITK/VTK Processing Endpoints
# ============================================================================

@app.route('/api/morphology', methods=['POST'])
def morphology_operation():
    """Apply morphological operations"""
    try:
        data = request.json
        
        response = requests.post(
            f"{ITK_VTK_URL}/api/morphology",
            json=data
        )
        
        return jsonify(response.json()), response.status_code
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/interpolate', methods=['POST'])
def interpolate_slices():
    """Interpolate between slices"""
    try:
        data = request.json
        
        response = requests.post(
            f"{ITK_VTK_URL}/api/interpolate",
            json=data
        )
        
        return jsonify(response.json()), response.status_code
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# Export Endpoints
# ============================================================================

@app.route('/api/export/dicom-seg/<instance_id>', methods=['GET'])
def export_dicom_seg(instance_id):
    """Export DICOM-SEG file"""
    try:
        # Get file from Orthanc
        response = requests.get(f"{ORTHANC_URL}/instances/{instance_id}/file")
        
        if response.status_code == 200:
            return send_file(
                BytesIO(response.content),
                mimetype='application/dicom',
                as_attachment=True,
                download_name=f'dicom-seg-{instance_id}.dcm'
            )
        else:
            return jsonify({'error': 'File not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# Statistics & Monitoring
# ============================================================================

@app.route('/api/stats', methods=['GET'])
def get_statistics():
    """Get application statistics"""
    try:
        # Get Orthanc statistics
        orthanc_stats = requests.get(f"{ORTHANC_URL}/statistics").json()
        
        # Get service health
        services_health = {
            'orthanc': check_service_health(ORTHANC_URL),
            'rt_utils': check_service_health(RT_UTILS_URL),
            'itk_vtk': check_service_health(ITK_VTK_URL),
            'orchestrator': check_service_health(ORCHESTRATOR_URL)
        }
        
        return jsonify({
            'orthanc': orthanc_stats,
            'services': services_health
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def check_service_health(url):
    """Check if a service is healthy"""
    try:
        response = requests.get(f"{url}/health", timeout=2)
        return {
            'status': 'healthy' if response.status_code == 200 else 'unhealthy',
            'response_time': response.elapsed.total_seconds()
        }
    except:
        return {'status': 'unreachable'}

# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
