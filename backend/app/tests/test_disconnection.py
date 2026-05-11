import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)

def test_health_endpoint_when_db_down():
    # Mock database failure in health check
    with patch("app.main.init_workspace_db") as mock_init:
        mock_init.side_effect = Exception("DB Connection Refused")
        
        # We don't want to restart the app, we want to test the /health endpoint logic.
        # But /health calls the init functions? Let's check main.py health_check.
        pass

@patch("app.main.init_workspace_db")
def test_startup_fails_when_db_down(mock_init):
    mock_init.side_effect = Exception("DB Down")
    
    # Testing the lifespan context manager directly or via TestClient startup
    # TestClient(app) triggers startup
    
    with pytest.raises(RuntimeError) as excinfo:
        with TestClient(app):
            pass
    assert "Mandatory database services unavailable" in str(excinfo.value)

def test_metrics_endpoint_responsiveness():
    # Verify metrics endpoint is reachable and returns expected structure
    resp = client.get("/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "active_requests" in data
    assert "memory" in data
    assert "uptime_seconds" in data
