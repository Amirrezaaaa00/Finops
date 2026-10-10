import os
from pathlib import Path

TEST_DB = Path(__file__).parent / "test_finops.db"
if TEST_DB.exists(): TEST_DB.unlink()
os.environ["FINOPS_DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["FINOPS_PROVIDER_MODE"] = "mock"

from fastapi.testclient import TestClient
from app.main import app


def test_health_and_summary():
    with TestClient(app) as client:
        h = client.get("/health")
        assert h.status_code == 200
        assert h.json()["status"] == "ok"
        s = client.get("/api/v1/summary?days=30")
        assert s.status_code == 200
        data = s.json()
        assert data["total_cost"] > 0
        assert data["active_projects"] == 4
        assert data["estimated_savings"] > 0


def test_odoo_export_schema():
    with TestClient(app) as client:
        r = client.get("/api/v1/odoo/export?days=30")
        assert r.status_code == 200
        data = r.json()
        assert data["schema_version"] == "1.0"
        assert len(data["records"]) > 100
        assert "summary" in data
        assert "recommendations" in data
