from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Patient, Study, Comparison, SyncLog
from schemas import PatientCreate, StudyCreate, ComparisonResponse, SyncStatusResponse
from datetime import datetime

def get_patients(db: Session, skip: int = 0, limit: int = 100):
    """Récupérer tous les patients"""
    return db.query(Patient).offset(skip).limit(limit).all()

def get_patient(db: Session, patient_id: str):
    """Récupérer un patient spécifique"""
    return db.query(Patient).filter(Patient.id == patient_id).first()

def create_patient(db: Session, patient: PatientCreate):
    """Créer un nouveau patient"""
    db_patient = Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

def get_studies(db: Session, patient_id: str = None, skip: int = 0, limit: int = 100):
    """Récupérer les études"""
    query = db.query(Study)
    if patient_id:
        query = query.filter(Study.patient_id == patient_id)
    return query.offset(skip).limit(limit).all()

def create_study(db: Session, study: StudyCreate):
    """Créer une nouvelle étude"""
    db_study = Study(**study.dict())
    db.add(db_study)
    db.commit()
    db.refresh(db_study)
    return db_study

def get_comparisons(db: Session, skip: int = 0, limit: int = 100):
    """Récupérer les comparaisons"""
    return db.query(Comparison).offset(skip).limit(limit).all()

def create_comparison(db: Session, comparison_data: dict):
    """Créer une nouvelle comparaison"""
    db_comparison = Comparison(**comparison_data)
    db.add(db_comparison)
    db.commit()
    db.refresh(db_comparison)
    return db_comparison

def create_sync_log(db: Session, service: str, action: str, status: str, message: str, details: dict = None):
    """Créer un log de synchronisation"""
    log = SyncLog(
        service=service,
        action=action,
        status=status,
        message=message,
        details=details or {}
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def get_sync_status(db: Session) -> SyncStatusResponse:
    """Récupérer le statut de synchronisation"""
    total_patients = db.query(func.count(Patient.id)).scalar() or 0
    synchronized_patients = db.query(func.count(Patient.id)).filter(Patient.synchronized == True).scalar() or 0
    pending_patients = total_patients - synchronized_patients
    
    total_studies = db.query(func.count(Study.id)).scalar() or 0
    synced_studies = db.query(func.count(Comparison.id)).filter(Comparison.sync_status == "completed").scalar() or 0
    
    last_sync_log = db.query(SyncLog).order_by(SyncLog.timestamp.desc()).first()
    last_sync = last_sync_log.timestamp if last_sync_log else None
    
    return SyncStatusResponse(
        total_patients=total_patients,
        synchronized_patients=synchronized_patients,
        pending_patients=pending_patients,
        total_studies=total_studies,
        synced_studies=synced_studies,
        last_sync=last_sync,
        next_sync=None  # À calculer basé sur SYNC_INTERVAL
    )
