"""
Tests pour les schemas Pydantic
"""
import pytest
from schemas import PatientBase, StudyBase
from pydantic import ValidationError

def test_patient_base_schema():
    """Test du schema PatientBase"""
    patient = PatientBase(
        name="Test Patient",
        patient_id="TEST_001"
    )
    assert patient.patient_id == "TEST_001"
    assert patient.name == "Test Patient"

def test_study_base_schema():
    """Test du schema StudyBase"""
    study = StudyBase(
        study_uid="1.2.3.4.5",
        study_description="Test Study",
        study_date="20240101",
        patient_id="TEST_001",
        patient_name="Test Patient"
    )
    assert study.study_uid == "1.2.3.4.5"
    assert study.study_description == "Test Study"

def test_patient_validation_error():
    """Test validation erreur Patient"""
    try:
        PatientBase(name="Test", patient_id=None)
        assert False, "Should raise ValidationError"
    except ValidationError:
        assert True

def test_study_validation_success():
    """Test validation réussie Study"""
    study = StudyBase(
        study_uid="UID123",
        study_description="",
        study_date="20240101",
        patient_id="P001",
        patient_name="Patient"
    )
    assert study.study_uid == "UID123"
