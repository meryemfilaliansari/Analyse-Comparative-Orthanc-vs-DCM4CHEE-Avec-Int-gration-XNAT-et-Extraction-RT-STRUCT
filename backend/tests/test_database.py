"""
Tests pour les modèles database
"""
import pytest
from models import Study, Patient

def test_patient_model():
    """Test du modèle Patient"""
    assert hasattr(Patient, '__tablename__')
    assert Patient.__tablename__ == 'patients'

def test_study_model():
    """Test du modèle Study"""
    assert hasattr(Study, '__tablename__')
    assert Study.__tablename__ == 'studies'

def test_patient_repr():
    """Test de la représentation Patient"""
    patient = Patient()
    assert 'Patient' in str(type(patient))

def test_study_repr():
    """Test de la représentation Study"""
    study = Study()
    assert 'Study' in str(type(study))
