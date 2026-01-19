from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    services: Dict[str, str]

class PatientBase(BaseModel):
    name: str
    birth_date: Optional[str] = None
    sex: Optional[str] = None
    patient_id: str

class PatientCreate(PatientBase):
    pass

class PatientResponse(PatientBase):
    id: str
    dcm4chee_id: Optional[str] = None
    orthanc_id: Optional[str] = None
    synchronized: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class StudyBase(BaseModel):
    study_uid: str
    study_date: Optional[datetime] = None
    study_description: Optional[str] = None

class StudyCreate(StudyBase):
    patient_id: str

class StudyResponse(StudyBase):
    id: str
    patient_id: str
    dcm4chee_id: Optional[str] = None
    orthanc_id: Optional[str] = None
    image_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ComparisonResponse(BaseModel):
    id: str
    study_id: str
    dcm4chee_images: int
    orthanc_images: int
    dcm4chee_response_time: Optional[float] = None
    orthanc_response_time: Optional[float] = None
    dcm4chee_success: bool
    orthanc_success: bool
    differences: Dict[str, Any]
    sync_status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SyncStatusResponse(BaseModel):
    total_patients: int
    synchronized_patients: int
    pending_patients: int
    total_studies: int
    synced_studies: int
    last_sync: Optional[datetime] = None
    next_sync: Optional[datetime] = None

class AnnotationBase(BaseModel):
    annotation_type: str
    data: Dict[str, Any]

class AnnotationCreate(AnnotationBase):
    study_id: str
    series_id: str
    instance_id: str

class AnnotationResponse(AnnotationCreate):
    id: str
    annotator_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    username: str
    email: str
    full_name: str
    role: str

class UserResponse(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
