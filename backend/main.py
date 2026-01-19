import os
import logging
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime
import httpx
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

from database import engine, SessionLocal, Base
from models import Patient, Study, Comparison, SyncLog
from schemas import (
    PatientResponse, StudyResponse, ComparisonResponse,
    SyncStatusResponse, HealthResponse
)
from crud import (
    get_patients, create_patient, get_studies, get_comparisons,
    create_sync_log, get_sync_status
)
from sync_service import SyncService
from prometheus_client import Counter, Histogram, generate_latest

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration des URLs des services PACS
dcm4chee_url = os.getenv('DCM4CHEE_URL', 'http://localhost:8080')
orthanc_url = os.getenv('ORTHANC_URL', 'http://localhost:8042')
xnat_url = os.getenv('XNAT_URL', 'http://localhost:8090')

# Prometheus metrics
requests_total = Counter(
    'pacs_requests_total',
    'Total requests',
    ['method', 'endpoint']
)
request_duration = Histogram(
    'pacs_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)
sync_errors = Counter(
    'pacs_sync_errors_total',
    'Total sync errors',
    ['service']
)
pacs_availability = Counter(
    'pacs_availability',
    'Service availability',
    ['service']
)

# Création des tables
Base.metadata.create_all(bind=engine)

# Service de synchronisation
sync_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global sync_service
    sync_service = SyncService(
        dcm4chee_url=os.getenv('DCM4CHEE_URL', 'http://localhost:8080'),
        orthanc_url=os.getenv('ORTHANC_URL', 'http://localhost:8042'),
        xnat_url=os.getenv('XNAT_URL', 'http://localhost:8090'),
        sync_interval=int(os.getenv('SYNC_INTERVAL', '60'))
    )
    
    # Démarrer la synchronisation en background
    sync_task = asyncio.create_task(sync_service.start_sync_loop())
    logger.info("Sync service started")
    
    yield
    
    # Shutdown
    sync_task.cancel()
    try:
        await sync_task
    except asyncio.CancelledError:
        logger.info("Sync service stopped")

app = FastAPI(
    title="PACS Multi-Systèmes",
    description="Plateforme intégrée de comparaison et d'analyse médicale DICOM",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Health endpoint
@app.get("/health", response_model=HealthResponse)
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Vérifier la santé de tous les services"""
    health_status = {}
    
    # SQLite local
    try:
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        health_status['database'] = 'healthy (SQLite)'
        db.close()
    except Exception as e:
        health_status['database'] = f'unhealthy: {str(e)}'
    
    # Vérifier DCM4CHEE
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get("http://localhost:8080/dcm4chee-arc/ui2/", timeout=10)
            health_status['dcm4chee'] = 'healthy' if response.status_code == 200 else 'unhealthy'
    except Exception as e:
        health_status['dcm4chee'] = f'unhealthy: {type(e).__name__}'
        logger.error(f"DCM4CHEE health check failed: {type(e).__name__} - {e}")
    
    # Vérifier Orthanc
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get("http://localhost:8042/system", timeout=10)
            health_status['orthanc'] = 'healthy' if response.status_code == 200 else 'unhealthy'
    except Exception as e:
        health_status['orthanc'] = f'unhealthy: {type(e).__name__}'
        logger.error(f"Orthanc health check failed: {type(e).__name__} - {e}")
    
    # Vérifier XNAT
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get("http://localhost:8090", timeout=10)
            health_status['xnat'] = 'healthy' if response.status_code == 200 else 'unhealthy'
    except Exception as e:
        health_status['xnat'] = f'unhealthy: {type(e).__name__}'
        logger.error(f"XNAT health check failed: {type(e).__name__} - {e}")
    
    all_healthy = all(v == 'healthy' for v in health_status.values())
    
    return HealthResponse(
        status='healthy' if all_healthy else 'degraded',
        timestamp=datetime.utcnow(),
        services=health_status
    )

# Patients endpoints
@app.get("/api/patients", response_model=list[PatientResponse])
async def list_patients(db = Depends(get_db)):
    """Récupérer tous les patients"""
    requests_total.labels(method='GET', endpoint='/api/patients').inc()
    return get_patients(db)

@app.post("/api/patients/sync")
async def sync_patients(db = Depends(get_db)):
    """Forcer la synchronisation des patients entre les PACS"""
    try:
        result = await sync_service.sync_patients()
        return {"status": "success", "synced": result}
    except Exception as e:
        sync_errors.labels(service='patients').inc()
        logger.error(f"Patient sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Studies endpoints
@app.get("/api/studies", response_model=list[StudyResponse])
async def list_studies(patient_id: str = None, db = Depends(get_db)):
    """Récupérer les études d'un patient"""
    requests_total.labels(method='GET', endpoint='/api/studies').inc()
    return get_studies(db, patient_id)

@app.get("/api/studies/{study_id}/comparison", response_model=ComparisonResponse)
async def get_study_comparison(study_id: str, db = Depends(get_db)):
    """Comparer une étude entre DCM4CHEE et Orthanc"""
    requests_total.labels(method='GET', endpoint='/api/studies/comparison').inc()
    comparison = db.query(Comparison).filter(Comparison.study_id == study_id).first()
    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found")
    return comparison

# Comparisons endpoints
@app.get("/api/comparisons", response_model=list[ComparisonResponse])
async def list_comparisons(db = Depends(get_db)):
    """Récupérer toutes les comparaisons"""
    requests_total.labels(method='GET', endpoint='/api/comparisons').inc()
    return get_comparisons(db)

@app.post("/api/comparisons/generate")
async def generate_comparisons(db = Depends(get_db)):
    """Générer les comparaisons pour tous les patients"""
    try:
        count = await sync_service.generate_comparisons()
        return {"status": "success", "comparisons_generated": count}
    except Exception as e:
        sync_errors.labels(service='comparisons').inc()
        logger.error(f"Comparison generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Sync status endpoints
@app.get("/api/sync/status", response_model=SyncStatusResponse)
async def get_sync_status_endpoint(db = Depends(get_db)):
    """Récupérer le statut de la synchronisation"""
    requests_total.labels(method='GET', endpoint='/api/sync/status').inc()
    return get_sync_status(db)

@app.get("/api/sync/history")
async def get_sync_history(limit: int = 50, db = Depends(get_db)):
    """Récupérer l'historique de synchronisation"""
    requests_total.labels(method='GET', endpoint='/api/sync/history').inc()
    logs = db.query(SyncLog).order_by(SyncLog.timestamp.desc()).limit(limit).all()
    return logs

# Anonymization endpoints
@app.post("/api/anonymize/study/{study_id}")
async def anonymize_study(study_id: str, db = Depends(get_db)):
    """Router une étude vers XNAT pour anonymisation"""
    try:
        result = await sync_service.anonymize_study(study_id)
        return {"status": "success", "anonymized_id": result}
    except Exception as e:
        sync_errors.labels(service='xnat').inc()
        logger.error(f"Anonymization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Métriques Prometheus"""
    return generate_latest()

# Statistics endpoints
@app.get("/api/statistics")
async def get_statistics(db = Depends(get_db)):
    """Statistiques globales du système"""
    requests_total.labels(method='GET', endpoint='/api/statistics').inc()
    
    total_patients = db.query(Patient).count()
    total_studies = db.query(Study).count()
    total_comparisons = db.query(Comparison).count()
    
    return {
        "total_patients": total_patients,
        "total_studies": total_studies,
        "total_comparisons": total_comparisons,
        "timestamp": datetime.utcnow()
    }

@app.get("/api/orthanc/statistics")
async def get_orthanc_statistics():
    """Statistiques Orthanc via proxy"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{orthanc_url}/statistics")
            if response.status_code == 200:
                return response.json()
            return {"error": "Orthanc unavailable", "status_code": response.status_code}
    except Exception as e:
        return {"error": str(e), "CountPatients": 0, "CountStudies": 0, "CountInstances": 0}

@app.get("/api/orthanc/system")
async def get_orthanc_system():
    """Informations système Orthanc via proxy"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{orthanc_url}/system")
            if response.status_code == 200:
                return response.json()
            return {"error": "Orthanc unavailable"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/orthanc/plugins")
async def get_orthanc_plugins():
    """Liste des plugins Orthanc via proxy"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{orthanc_url}/plugins")
            if response.status_code == 200:
                return response.json()
            return []
    except Exception as e:
        return []

@app.get("/api/dcm4chee/statistics")
async def get_dcm4chee_statistics():
    """Statistiques DCM4CHEE via proxy"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Récupérer les patients
            patients_response = await client.get(f"{dcm4chee_url}/dcm4chee-arc/aets/DCM4CHEE/rs/patients")
            patients_count = 0
            if patients_response.status_code == 200:
                patients = patients_response.json()
                patients_count = len(patients)
            
            # Récupérer les études
            studies_response = await client.get(f"{dcm4chee_url}/dcm4chee-arc/aets/DCM4CHEE/rs/studies")
            studies_count = 0
            instances_count = 0
            if studies_response.status_code == 200:
                studies = studies_response.json()
                studies_count = len(studies)
                # Compter les instances
                for study in studies:
                    try:
                        series_count = study.get('00201206', {}).get('Value', [0])[0]
                        instances_count += int(series_count) if series_count else 0
                    except:
                        pass
            
            return {
                "CountPatients": patients_count,
                "CountStudies": studies_count,
                "CountInstances": instances_count,
                "TotalDiskSizeMB": 0  # Non disponible via DICOMweb
            }
    except Exception as e:
        return {"error": str(e), "CountPatients": 0, "CountStudies": 0, "CountInstances": 0}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
