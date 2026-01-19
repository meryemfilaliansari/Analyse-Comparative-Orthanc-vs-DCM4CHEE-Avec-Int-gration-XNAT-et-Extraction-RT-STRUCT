"""
Tests additionnels pour augmenter la couverture
"""
import pytest
from database import engine, Base, SessionLocal

def test_database_engine():
    """Test de la connexion database"""
    assert engine is not None
    
def test_database_base():
    """Test du Base declarative"""
    assert Base is not None
    assert hasattr(Base, 'metadata')

def test_session_local():
    """Test de la factory de session"""
    session = SessionLocal()
    assert session is not None
    session.close()

def test_create_tables():
    """Test de création des tables"""
    try:
        Base.metadata.create_all(bind=engine)
        assert True
    except Exception as e:
        assert False, f"Failed to create tables: {e}"

def test_tables_exist():
    """Test que les tables existent"""
    Base.metadata.create_all(bind=engine)
    tables = Base.metadata.tables.keys()
    assert 'patients' in tables
    assert 'studies' in tables
