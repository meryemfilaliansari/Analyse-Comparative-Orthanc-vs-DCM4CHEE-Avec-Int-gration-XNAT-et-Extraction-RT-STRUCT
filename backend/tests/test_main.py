"""
Tests pour l'API principale FastAPI
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    """Test du endpoint /api/health"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data

def test_statistics_endpoint():
    """Test du endpoint /api/statistics"""
    response = client.get("/api/statistics")
    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data

def test_root_redirect():
    """Test de la redirection root"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code in [200, 307, 404]

def test_invalid_endpoint():
    """Test d'un endpoint inexistant"""
    response = client.get("/api/invalid_endpoint_xyz")
    assert response.status_code == 404

def test_metrics_endpoint():
    """Test du endpoint /metrics"""
    response = client.get("/metrics")
    assert response.status_code == 200
