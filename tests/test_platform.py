import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app import models, schemas
from backend.app.scanner import simulate_scan
from backend.app.gap_analysis import evaluate_all_rules
from backend.app.advisor import get_ai_remediation_advice
from backend.app.reporter import generate_ncsc_se_pdf

# 1. SETUP IN-MEMORY SQLITE FOR RIGOROUS SANDBOX TESTING
TEST_DATABASE_URL = "sqlite:///./test_sandbox.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override FastAPI database dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables after test runs
    Base.metadata.drop_all(bind=engine)
    engine.dispose() # Dispose connection pool to release lock on Windows
    if os.path.exists("./test_sandbox.db"):
        os.remove("./test_sandbox.db")

# ========================================================================
# 🧪 PLATFORM AUTOMATED TEST SUITE (11 CRITICAL CONTROLS)
# ========================================================================

def test_1_models_asset_instantiation():
    """Verify that Asset models compile parameters and sectors."""
    asset = models.Asset(
        ip="10.0.0.5",
        hostname="ad-controller.test",
        scope_sector="Public Administration",
        in_scope=True,
        criticality="Critical",
        ports="80,443"
    )
    assert asset.ip == "10.0.0.5"
    assert asset.hostname == "ad-controller.test"
    assert asset.in_scope is True
    assert asset.criticality == "Critical"

def test_2_models_gap_analysis_instantiation():
    """Verify GapAnalysis schemas holding compliance statuses."""
    gap = models.GapAnalysis(
        article_id="Art 21.2h",
        category="Cryptography",
        control_name="Encryption Policy",
        score=75,
        status="Partial",
        remediation_steps="Implement HTTPS"
    )
    assert gap.article_id == "Art 21.2h"
    assert gap.score == 75
    assert gap.status == "Partial"

def test_3_database_sqlite_sandbox_write():
    """Verify basic session insertion operations."""
    db = TestingSessionLocal()
    try:
        setting = models.SystemSettings(scan_target="172.16.0.0/16")
        db.add(setting)
        db.commit()
        db.refresh(setting)
        assert setting.id is not None
        assert setting.scan_target == "172.16.0.0/16"
    finally:
        db.close()

def test_4_scanner_simulation_maps_assets():
    """Verify simulation runner adds mock subnet perimeters correctly."""
    db = TestingSessionLocal()
    try:
        # Trigger mock sweep
        settings = models.SystemSettings(scan_target="192.168.1.0/24")
        simulate_scan(db, "192.168.1.0/24", settings)
        assets = db.query(models.Asset).all()
        # Verify assets are added
        assert len(assets) > 0
        # Verify Critical AD sector mapping
        ad_node = db.query(models.Asset).filter(models.Asset.hostname.like("%ad-domain-controller%")).first()
        assert ad_node is not None
        assert ad_node.criticality == "Critical"
        assert ad_node.in_scope is True
    finally:
        db.close()

def test_5_gap_analysis_adjusts_crypto_scores():
    """Verify dynamic scorer reduces encryption scores if unencrypted ports exist."""
    db = TestingSessionLocal()
    try:
        settings = models.SystemSettings(scan_target="192.168.1.0/24")
        simulate_scan(db, "192.168.1.0/24", settings)
        evaluate_all_rules(db)
        crypto_gap = db.query(models.GapAnalysis).filter(models.GapAnalysis.article_id == "Art 21.2h").first()
        assert crypto_gap is not None
        # Score must drop from 35 default because port 80/8080 is simulated active
        assert crypto_gap.score <= 35
        assert "Insecure HTTP services" in crypto_gap.comments
    finally:
        db.close()

def test_6_ai_advisor_local_semantic_rag():
    """Verify local keywords search fallback resolves suggestions."""
    db = TestingSessionLocal()
    try:
        advice = get_ai_remediation_advice("encryption and secure communication protocols", db)
        assert advice is not None
        assert "Article 21.2h" in advice["response"]
        assert "TLS 1.3" in advice["response"]
    finally:
        db.close()

def test_7_reportlab_msb_pdf_generation():
    """Verify PDF Stream compiler returns robust byte streams."""
    db = TestingSessionLocal()
    try:
        pdf_buffer = generate_ncsc_se_pdf(db)
        pdf_bytes = pdf_buffer.getvalue()
        assert len(pdf_bytes) > 0
        # Verify PDF header bytes
        assert pdf_bytes.startswith(b"%PDF")
    finally:
        db.close()

def test_8_api_root_endpoint_jinja2():
    """Verify GET / successfully serves the backup dashboard UI."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "NIS2 CYBERSHIELD" in response.text

def test_9_api_get_discovered_assets():
    """Verify GET /api/v1/assets returns deserialized list schemas."""
    response = client.get("/api/v1/assets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "ip" in data[0]

def test_10_api_get_dashboard_statistics():
    """Verify telemetry statistics schema returns properly parsed metrics."""
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert "overall_compliance_score" in data
    assert "scanned_assets_count" in data
    assert "gap_breakdown" in data
    assert isinstance(data["gap_breakdown"], dict)

def test_11_api_update_gap_slider_recalculation():
    """Verify PUT /api/v1/gap-analysis updates maturity scores and appends history."""
    update_data = {"score": 85, "comments": "Upgraded SSL certs in Q2."}
    response = client.put("/api/v1/gap-analysis/Art 21.2h", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 85
    assert data["status"] == "Compliant"
    assert data["comments"] == "Upgraded SSL certs in Q2."
