"""
Tests pour les modèles complets
"""
import pytest
from models import Patient, Study, Comparison, Annotation, User, SyncLog

def test_all_models_exist():
    """Test que tous les modèles existent"""
    assert Patient is not None
    assert Study is not None
    assert Comparison is not None
    assert Annotation is not None
    assert User is not None
    assert SyncLog is not None

def test_patient_table_name():
    """Test du nom de table Patient"""
    assert Patient.__tablename__ == 'patients'

def test_study_table_name():
    """Test du nom de table Study"""
    assert Study.__tablename__ == 'studies'

def test_comparison_table_name():
    """Test du nom de table Comparison"""
    assert Comparison.__tablename__ == 'comparisons'

def test_annotation_table_name():
    """Test du nom de table Annotation"""
    assert Annotation.__tablename__ == 'annotations'

def test_user_table_name():
    """Test du nom de table User"""
    assert User.__tablename__ == 'users'

def test_synclog_table_name():
    """Test du nom de table SyncLog"""
    assert SyncLog.__tablename__ == 'sync_logs'

def test_models_have_columns():
    """Test que les modèles ont des colonnes"""
    assert hasattr(Patient, '__table__')
    assert hasattr(Study, '__table__')
    assert len(Patient.__table__.columns) > 0
    assert len(Study.__table__.columns) > 0
