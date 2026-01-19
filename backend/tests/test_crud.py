"""
Tests pour les opérations CRUD
"""
import pytest
from crud import get_patients, get_studies, get_comparisons
from database import SessionLocal

def test_get_patients():
    """Test récupération patients"""
    db = SessionLocal()
    try:
        patients = get_patients(db, skip=0, limit=10)
        assert isinstance(patients, list)
    finally:
        db.close()

def test_get_studies():
    """Test récupération études"""
    db = SessionLocal()
    try:
        studies = get_studies(db, skip=0, limit=10)
        assert isinstance(studies, list)
    finally:
        db.close()

def test_get_comparisons():
    """Test récupération comparaisons"""
    db = SessionLocal()
    try:
        comparisons = get_comparisons(db, skip=0, limit=10)
        assert isinstance(comparisons, list)
    finally:
        db.close()
