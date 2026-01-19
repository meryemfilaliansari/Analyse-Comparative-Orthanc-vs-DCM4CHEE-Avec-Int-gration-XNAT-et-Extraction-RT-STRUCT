from sqlalchemy import Column, String, Integer, DateTime, Float, JSON, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(String, primary_key=True)
    name = Column(String)
    birth_date = Column(String)
    sex = Column(String)
    patient_id = Column(String, unique=True)
    dcm4chee_id = Column(String)
    orthanc_id = Column(String)
    synchronized = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    studies = relationship("Study", back_populates="patient")

class Study(Base):
    __tablename__ = "studies"
    
    id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"))
    study_uid = Column(String)
    study_date = Column(DateTime)
    study_time = Column(String)
    study_description = Column(String)
    dcm4chee_id = Column(String)
    orthanc_id = Column(String)
    image_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    patient = relationship("Patient", back_populates="studies")
    comparisons = relationship("Comparison", back_populates="study")

class Series(Base):
    __tablename__ = "series"
    
    id = Column(String, primary_key=True)
    study_id = Column(String, ForeignKey("studies.id"))
    series_uid = Column(String)
    series_number = Column(String)
    modality = Column(String)
    series_description = Column(String)
    dcm4chee_id = Column(String)
    orthanc_id = Column(String)
    instance_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Instance(Base):
    __tablename__ = "instances"
    
    id = Column(String, primary_key=True)
    series_id = Column(String)
    sop_instance_uid = Column(String)
    dcm4chee_id = Column(String)
    orthanc_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Comparison(Base):
    __tablename__ = "comparisons"
    
    id = Column(String, primary_key=True)
    study_id = Column(String, ForeignKey("studies.id"))
    dcm4chee_images = Column(Integer, default=0)
    orthanc_images = Column(Integer, default=0)
    dcm4chee_response_time = Column(Float)
    orthanc_response_time = Column(Float)
    dcm4chee_success = Column(Boolean, default=False)
    orthanc_success = Column(Boolean, default=False)
    differences = Column(JSON, default={})
    sync_status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    study = relationship("Study", back_populates="comparisons")

class SyncLog(Base):
    __tablename__ = "sync_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    service = Column(String)  # dcm4chee, orthanc, xnat
    action = Column(String)  # sync, upload, anonymize
    status = Column(String)  # success, error, pending
    message = Column(Text)
    details = Column(JSON, default={})
    timestamp = Column(DateTime, default=datetime.utcnow)

class Annotation(Base):
    __tablename__ = "annotations"
    
    id = Column(String, primary_key=True)
    study_id = Column(String)
    series_id = Column(String)
    instance_id = Column(String)
    annotator_id = Column(String)
    annotation_type = Column(String)  # segmentation, measurement, comment
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    full_name = Column(String)
    role = Column(String)  # admin, radiologist, researcher
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
