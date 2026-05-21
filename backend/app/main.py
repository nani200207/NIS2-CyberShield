import os
import datetime
from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from backend.app.database import engine, Base, get_db
from backend.app import models, schemas
from backend.app.scanner import start_background_scan, simulate_scan, evaluate_all_rules
from backend.app.advisor import get_ai_remediation_advice
from backend.app.reporter import generate_ncsc_se_pdf
from backend.app.scheduler import init_scheduler, update_scheduler_interval

# 1. Initialize DB tables
Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="backend/app/templates")

app = FastAPI(
    title="NIS2 CyberShield Compliance Platform API",
    description="Backend services powering Asset Discovery, NIS2 Article 21 Gap Analysis, AI Remediation, and Swedish Regulator PDF Auditing.",
    version="1.0.0"
)

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    """
    Serves the beautiful NIS2 compliance dashboard application.
    """
    return templates.TemplateResponse(request, "index.html")


# 2. Configure CORS for smooth React Vite local connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow development ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Startup Event
@app.on_event("startup")
def startup_event():
    print("FastAPI server starting...")
    # Initialize background scanning scheduler
    init_scheduler()
    
    # Pre-populate gap analysis controls if database is empty so the frontend has context instantly
    db = next(get_db())
    try:
        gaps = db.query(models.GapAnalysis).all()
        if not gaps:
            print("Database empty. Populating default NIS2 Gap Analysis requirements and sample history...")
            evaluate_all_rules(db)
    finally:
        db.close()

# --- SCANNER ENDPOINTS ---

@app.post("/api/v1/scan", response_model=Dict[str, str])
def trigger_network_scan(
    target: str = Query("192.168.1.0/24", description="IP subnet target"),
    real_scan: bool = Query(False, description="True for real sockets scan, False for detailed simulation"),
    db: Session = Depends(get_db)
):
    """
    Triggers a manual asset discovery scan. Runs in a background thread to prevent API blocking.
    """
    settings = db.query(models.SystemSettings).first()
    if not settings:
        settings = models.SystemSettings(scan_target=target)
        db.add(settings)
    else:
        settings.scan_target = target
    db.commit()
    
    # Start scanner thread
    start_background_scan(db, target, real_scan)
    return {"message": f"Scan initiated for {target} in background. Monitoring progress via logs endpoint."}

@app.get("/api/v1/scan/logs", response_model=List[schemas.ScanLogResponse])
def get_scan_logs(limit: int = 50, db: Session = Depends(get_db)):
    """
    Returns recent scanning terminal console lines (newest first).
    """
    logs = db.query(models.ScanLog).order_by(models.ScanLog.timestamp.desc()).limit(limit).all()
    return logs

@app.post("/api/v1/scan/logs/clear", response_model=Dict[str, str])
def clear_scan_logs(db: Session = Depends(get_db)):
    """
    Clears all stored scan logs from the system console.
    """
    db.query(models.ScanLog).delete()
    db.commit()
    return {"message": "Scan console history successfully wiped."}

# --- ASSET DISCOVERY ENDPOINTS ---

@app.get("/api/v1/assets", response_model=List[schemas.AssetResponse])
def get_assets(db: Session = Depends(get_db)):
    """
    Fetches all discovered IT network assets.
    """
    assets = db.query(models.Asset).all()
    return assets

@app.get("/api/v1/assets/in-scope", response_model=List[schemas.AssetResponse])
def get_in_scope_assets(db: Session = Depends(get_db)):
    """
    Retrieves assets categorized as In Scope of NIS2 Directive sectors.
    """
    assets = db.query(models.Asset).filter(models.Asset.in_scope == True).all()
    return assets

# --- GAP ANALYSIS ENGINE ENDPOINTS ---

@app.get("/api/v1/gap-analysis", response_model=List[schemas.GapAnalysisResponse])
def get_gap_analysis(db: Session = Depends(get_db)):
    """
    Fetches the Article 21 compliance gaps and audits.
    """
    gaps = db.query(models.GapAnalysis).all()
    return gaps

@app.put("/api/v1/gap-analysis/{article_id}", response_model=schemas.GapAnalysisResponse)
def update_gap_control(
    article_id: str, 
    update_data: schemas.GapAnalysisUpdate, 
    db: Session = Depends(get_db)
):
    """
    Allows auditors or CISOs to manually review, overwrite compliance scores,
    or append audit comments to individual Article 21 requirements.
    """
    gap = db.query(models.GapAnalysis).filter(models.GapAnalysis.article_id == article_id).first()
    if not gap:
        raise HTTPException(status_code=404, detail=f"NIS2 Control ID {article_id} not found.")
        
    if update_data.score is not None:
        if not (0 <= update_data.score <= 100):
            raise HTTPException(status_code=400, detail="Maturity score must be between 0 and 100.")
        gap.score = update_data.score
        # Compute status
        if gap.score >= 80:
            gap.status = "Compliant"
        elif gap.score >= 40:
            gap.status = "Partial"
        else:
            gap.status = "Non-Compliant"
            
    if update_data.comments is not None:
        gap.comments = update_data.comments
        
    if update_data.remediation_steps is not None:
        gap.remediation_steps = update_data.remediation_steps
        
    db.commit()
    
    # Recalculate historical overall compliance average
    all_gaps = db.query(models.GapAnalysis).all()
    avg_score = sum(g.score for g in all_gaps) / len(all_gaps) if all_gaps else 0.0
    
    # Save compliance point
    today = datetime.date.today()
    existing_history = db.query(models.ComplianceHistory).filter(
        func.date(models.ComplianceHistory.recorded_at) == today
    ).first()
    
    if existing_history:
        existing_history.score = round(avg_score, 1)
        existing_history.recorded_at = datetime.datetime.utcnow()
    else:
        history = models.ComplianceHistory(
            score=round(avg_score, 1),
            scanned_assets=db.query(models.Asset).count(),
            critical_gaps=db.query(models.GapAnalysis).filter(models.GapAnalysis.status == "Non-Compliant").count(),
            recorded_at=datetime.datetime.utcnow()
        )
        db.add(history)
    db.commit()
    
    db.refresh(gap)
    return gap

# --- AI REMEDIATION ADVISOR ENDPOINTS ---

@app.post("/api/v1/advisor/query", response_model=schemas.AIAdvisorResponse)
def query_ai_advisor(query_body: schemas.AIAdvisorQuery, db: Session = Depends(get_db)):
    """
    RAG-enabled LLM advisor. Takes natural language queries, injects database compliance status,
    and returns a beautifully structured markdown plain-language solution.
    """
    if not query_body.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")
        
    advice = get_ai_remediation_advice(query_body.query, db)
    return advice

# --- AUTOMATED PDF REPORT ENDPOINTS ---

@app.get("/api/v1/report/pdf")
def get_pdf_report(db: Session = Depends(get_db)):
    """
    Generates and streams a professional audit-grade PDF formatted for Swedish Regulators (MSB).
    """
    pdf_buffer = generate_ncsc_se_pdf(db)
    
    filename = f"NIS2_Compliance_Audit_{datetime.date.today().strftime('%Y_%m_%d')}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# --- SYSTEM CONFIG ENDPOINTS ---

@app.get("/api/v1/settings", response_model=schemas.SystemSettingsResponse)
def get_system_settings(db: Session = Depends(get_db)):
    """
    Retrieves global platform credentials and settings.
    """
    settings = db.query(models.SystemSettings).first()
    if not settings:
        settings = models.SystemSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

@app.put("/api/v1/settings", response_model=schemas.SystemSettingsResponse)
def update_system_settings(update_body: schemas.SystemSettingsUpdate, db: Session = Depends(get_db)):
    """
    Saves global configuration keys and triggers dynamic background scheduler adjustments.
    """
    settings = db.query(models.SystemSettings).first()
    if not settings:
        settings = models.SystemSettings()
        db.add(settings)
        db.commit()
        
    if update_body.scan_target is not None:
        settings.scan_target = update_body.scan_target
    if update_body.shodan_key is not None:
        settings.shodan_key = update_body.shodan_key
    if update_body.gemini_key is not None:
        settings.gemini_key = update_body.gemini_key
    if update_body.slack_webhook is not None:
        settings.slack_webhook = update_body.slack_webhook
    if update_body.monitoring_active is not None:
        settings.monitoring_active = update_body.monitoring_active
        
    if update_body.scan_frequency is not None:
        settings.scan_frequency = update_body.scan_frequency
        # Reschedule APScheduler dynamically!
        update_scheduler_interval(settings.scan_frequency)
        
    db.commit()
    db.refresh(settings)
    return settings

# --- DASHBOARD METRICS ENDPOINTS ---

@app.get("/api/v1/dashboard/stats", response_model=schemas.DashboardStats)
def get_dashboard_statistics(db: Session = Depends(get_db)):
    """
    Gathers complex analytics (overall compliance score, critical assets, heatmaps, and trends)
    specifically designed to fuel beautiful interactive React components.
    """
    # 1. Total gaps count
    gaps = db.query(models.GapAnalysis).all()
    avg_score = sum(g.score for g in gaps) / len(gaps) if gaps else 0.0
    critical_gaps_count = len([g for g in gaps if g.status == "Non-Compliant"])
    
    # 2. Assets counts
    assets = db.query(models.Asset).all()
    scanned_count = len(assets)
    in_scope_count = len([a for a in assets if a.in_scope])
    critical_assets = db.query(models.Asset).filter(models.Asset.criticality == "Critical").all()
    
    # 3. Gap breakdown by category (for donut charts)
    breakdown = {}
    for g in gaps:
        breakdown[g.category] = g.score
        
    # 4. History log trends (newest recorded last)
    history = db.query(models.ComplianceHistory).order_by(models.ComplianceHistory.recorded_at.asc()).all()
    
    return {
        "overall_compliance_score": round(avg_score, 1),
        "scanned_assets_count": scanned_count,
        "in_scope_assets_count": in_scope_count,
        "critical_gaps_count": critical_gaps_count,
        "gap_breakdown": breakdown,
        "history": history,
        "critical_assets": critical_assets
    }
