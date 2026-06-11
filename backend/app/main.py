import os
import datetime
import shutil
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks, Request, WebSocket, WebSocketDisconnect, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from backend.app.database import engine, Base, get_db, SessionLocal
from backend.app import models, schemas
from backend.app.scanner import start_background_scan, simulate_scan, evaluate_all_rules
from backend.app.advisor import get_ai_remediation_advice
from backend.app.reporter import generate_ncsc_se_pdf
from backend.app.scheduler import init_scheduler, update_scheduler_interval

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("FastAPI server starting...")
    # Initialize database tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize background scanning scheduler
    init_scheduler()
    
    # Pre-populate gap analysis controls if database is empty so the frontend has context instantly
    db = SessionLocal()
    try:
        # Seed default Demo Corporation organization
        default_org = db.query(models.Organization).filter(models.Organization.id == 1).first()
        if not default_org:
            print("Seeding default organization: Demo Corporation")
            default_org = models.Organization(id=1, name="Demo Corporation")
            db.add(default_org)
            db.commit()
            
        gaps = db.query(models.GapAnalysis).all()
        if not gaps:
            print("Database empty. Populating default NIS2 Gap Analysis requirements...")
            evaluate_all_rules(db, organization_id=1)
    finally:
        db.close()
    yield
    print("FastAPI server shutting down...")

templates = Jinja2Templates(directory="backend/app/templates")

app = FastAPI(
    title="NIS2 CyberShield Compliance Platform API",
    description="Backend services powering Asset Discovery, NIS2 Article 21 Gap Analysis, AI Remediation, and Swedish Regulator PDF Auditing.",
    version="1.0.0",
    lifespan=lifespan
)

from fastapi.staticfiles import StaticFiles
os.makedirs("uploads/evidence", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    """
    Serves the beautiful NIS2 compliance dashboard application.
    """
    return templates.TemplateResponse(request, "index.html")

# 2. Hardened CORS Middleware (resolves "*" security hole)
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000")
origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helpers for Multi-Tenancy database query mapping
def models_or_fallback_filter(model_class, organization_id: int):
    return (model_class.organization_id == organization_id) | (model_class.organization_id == None)

# --- SAAS MULTI-TENANT ORGANIZATIONS ENDPOINTS ---

@app.get("/api/v1/organizations", response_model=List[schemas.OrganizationResponse])
def get_organizations(db: Session = Depends(get_db)):
    """
    Fetches all registered SaaS organization tenants in the platform.
    """
    return db.query(models.Organization).all()

@app.post("/api/v1/organizations", response_model=schemas.OrganizationResponse)
def create_organization(org_data: schemas.OrganizationCreate, db: Session = Depends(get_db)):
    """
    Creates a new SaaS organization tenant and automatically seeds their Article 21 Gaps baseline.
    """
    existing = db.query(models.Organization).filter(models.Organization.name == org_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Organization name already exists.")
    
    new_org = models.Organization(name=org_data.name)
    db.add(new_org)
    db.commit()
    db.refresh(new_org)
    
    # Initialize default gaps for new organization
    evaluate_all_rules(db, organization_id=new_org.id)
    return new_org

# --- SCANNER & WEBSOCKET ENDPOINTS ---

@app.post("/api/v1/scan", response_model=Dict[str, str])
def trigger_network_scan(
    target: str = Query("10.100.4.0/24", description="IP subnet target"),
    real_scan: bool = Query(False, description="True for real sockets scan, False for detailed simulation"),
    org_id: int = Query(1, description="Tenant organization ID"),
    db: Session = Depends(get_db)
):
    """
    Triggers a manual asset discovery scan. Runs in a background thread to prevent API blocking.
    """
    settings = db.query(models.SystemSettings).filter(models.SystemSettings.organization_id == org_id).first()
    if not settings:
        settings = db.query(models.SystemSettings).filter(models.SystemSettings.id == 1).first()
        if not settings:
            settings = models.SystemSettings(organization_id=org_id, scan_target=target)
            db.add(settings)
        else:
            settings.scan_target = target
    else:
        settings.scan_target = target
    db.commit()
    
    start_background_scan(db, target, real_scan, organization_id=org_id)
    return {"message": f"Scan initiated for {target} in background. Stream logs via WebSocket."}

@app.websocket("/api/v1/scan/ws-logs")
async def websocket_logs(websocket: WebSocket, org_id: int = 1):
    """
    Persistent WebSocket streaming live scan terminal console traces to active clients.
    """
    await websocket.accept()
    db = SessionLocal()
    last_log_id = 0
    try:
        # First, send existing logs in order
        initial_logs = db.query(models.ScanLog).filter(
            models_or_fallback_filter(models.ScanLog, org_id)
        ).order_by(models.ScanLog.timestamp.asc()).all()
        
        for log in initial_logs:
            await websocket.send_json({
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "level": log.level,
                "message": log.message
            })
            if log.id > last_log_id:
                last_log_id = log.id
                
        # Stream new logs live character-by-character
        while True:
            new_logs = db.query(models.ScanLog).filter(
                models.ScanLog.id > last_log_id,
                models_or_fallback_filter(models.ScanLog, org_id)
            ).order_by(models.ScanLog.timestamp.asc()).all()
            
            for log in new_logs:
                await websocket.send_json({
                    "id": log.id,
                    "timestamp": log.timestamp.isoformat(),
                    "level": log.level,
                    "message": log.message
                })
                last_log_id = log.id
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass
    finally:
        db.close()

@app.post("/api/v1/scan/logs/clear", response_model=Dict[str, str])
def clear_scan_logs(org_id: int = Query(1), db: Session = Depends(get_db)):
    """
    Clears all stored scan logs from the system console.
    """
    db.query(models.ScanLog).filter(models_or_fallback_filter(models.ScanLog, org_id)).delete()
    db.commit()
    return {"message": "Scan console history successfully wiped."}

# --- ASSET DISCOVERY ENDPOINTS ---

@app.get("/api/v1/assets", response_model=List[schemas.AssetResponse])
def get_assets(org_id: int = Query(1), db: Session = Depends(get_db)):
    """
    Fetches discovered IT network assets scoped per SaaS organization.
    """
    return db.query(models.Asset).filter(models_or_fallback_filter(models.Asset, org_id)).all()

@app.get("/api/v1/assets/in-scope", response_model=List[schemas.AssetResponse])
def get_in_scope_assets(org_id: int = Query(1), db: Session = Depends(get_db)):
    """
    Retrieves assets categorized as In Scope of NIS2 Directive sectors.
    """
    return db.query(models.Asset).filter(
        models.Asset.in_scope == True,
        models_or_fallback_filter(models.Asset, org_id)
    ).all()

# --- GAP ANALYSIS & EVIDENCE UPLOADS ---

@app.get("/api/v1/gap-analysis", response_model=List[schemas.GapAnalysisResponse])
def get_gap_analysis(org_id: int = Query(1), db: Session = Depends(get_db)):
    """
    Fetches the Article 21 compliance gaps and audits scoped per SaaS organization.
    """
    return db.query(models.GapAnalysis).filter(models_or_fallback_filter(models.GapAnalysis, org_id)).all()

@app.put("/api/v1/gap-analysis/{article_id}", response_model=schemas.GapAnalysisResponse)
def update_gap_control(
    article_id: str, 
    update_data: schemas.GapAnalysisUpdate,
    org_id: int = Query(1),
    db: Session = Depends(get_db)
):
    """
    Allows auditors to review, overwrite compliance scores, or append comments to requirements.
    """
    gap = db.query(models.GapAnalysis).filter(
        models.GapAnalysis.article_id == article_id,
        models_or_fallback_filter(models.GapAnalysis, org_id)
    ).first()
    
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
    all_gaps = db.query(models.GapAnalysis).filter(models_or_fallback_filter(models.GapAnalysis, org_id)).all()
    avg_score = sum(g.score for g in all_gaps) / len(all_gaps) if all_gaps else 0.0
    
    today = datetime.date.today()
    existing_history = db.query(models.ComplianceHistory).filter(
        func.date(models.ComplianceHistory.recorded_at) == today,
        models_or_fallback_filter(models.ComplianceHistory, org_id)
    ).first()
    
    if existing_history:
        existing_history.score = round(avg_score, 1)
        existing_history.recorded_at = datetime.datetime.utcnow()
    else:
        history = models.ComplianceHistory(
            organization_id=org_id,
            score=round(avg_score, 1),
            scanned_assets=db.query(models.Asset).filter(models_or_fallback_filter(models.Asset, org_id)).count(),
            critical_gaps=db.query(models.GapAnalysis).filter(
                models.GapAnalysis.status == "Non-Compliant",
                models_or_fallback_filter(models.GapAnalysis, org_id)
            ).count(),
            recorded_at=datetime.datetime.utcnow()
        )
        db.add(history)
    db.commit()
    
    db.refresh(gap)
    return gap

@app.post("/api/v1/gap-analysis/{article_id}/evidence", response_model=schemas.GapAnalysisResponse)
def upload_evidence_file(
    article_id: str,
    file: UploadFile = File(...),
    org_id: int = Query(1),
    db: Session = Depends(get_db)
):
    """
    Saves auditor document proof (screenshots, policies) against a specific control.
    """
    gap = db.query(models.GapAnalysis).filter(
        models.GapAnalysis.article_id == article_id,
        models_or_fallback_filter(models.GapAnalysis, org_id)
    ).first()
    
    if not gap:
        raise HTTPException(status_code=404, detail=f"Gap Control {article_id} not found.")
        
    upload_dir = "uploads/evidence"
    os.makedirs(upload_dir, exist_ok=True)
    
    safe_filename = f"org_{org_id}_{article_id}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(upload_dir, safe_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    gap.evidence_file_path = f"uploads/evidence/{safe_filename}"
    db.commit()
    db.refresh(gap)
    return gap

# --- REMEDIATION TASK TRACKER ENDPOINTS ---

@app.get("/api/v1/tasks", response_model=List[schemas.RemediationTaskResponse])
def get_remediation_tasks(org_id: int = Query(1), db: Session = Depends(get_db)):
    """
    Fetches all active remediation tasks scoped to the organization.
    """
    return db.query(models.RemediationTask).filter(models_or_fallback_filter(models.RemediationTask, org_id)).all()

@app.post("/api/v1/tasks", response_model=schemas.RemediationTaskResponse)
def create_remediation_task(
    task_data: schemas.RemediationTaskCreate, 
    org_id: int = Query(1), 
    db: Session = Depends(get_db)
):
    """
    Schedules a new compliance remediation task on the Kanban board.
    """
    new_task = models.RemediationTask(
        organization_id=org_id,
        gap_id=task_data.gap_id,
        title=task_data.title,
        description=task_data.description,
        assignee=task_data.assignee,
        due_date=task_data.due_date,
        status=task_data.status
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@app.put("/api/v1/tasks/{task_id}", response_model=schemas.RemediationTaskResponse)
def update_remediation_task(
    task_id: int, 
    task_update: schemas.RemediationTaskUpdate, 
    db: Session = Depends(get_db)
):
    """
    Updates the assignee, due date, or Kanban status of a remediation task.
    """
    task = db.query(models.RemediationTask).filter(models.RemediationTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Remediation task not found.")
        
    if task_update.title is not None:
        task.title = task_update.title
    if task_update.description is not None:
        task.description = task_update.description
    if task_update.assignee is not None:
        task.assignee = task_update.assignee
    if task_update.due_date is not None:
        task.due_date = task_update.due_date
    if task_update.status is not None:
        task.status = task_update.status
        
    db.commit()
    db.refresh(task)
    return task

@app.delete("/api/v1/tasks/{task_id}", response_model=Dict[str, str])
def delete_remediation_task(task_id: int, db: Session = Depends(get_db)):
    """
    Deletes a completed or expired remediation task from the pipeline.
    """
    task = db.query(models.RemediationTask).filter(models.RemediationTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Remediation task not found.")
    db.delete(task)
    db.commit()
    return {"message": "Task successfully deleted."}

# --- AI REMEDIATION ADVISOR ENDPOINTS ---

@app.post("/api/v1/advisor/query", response_model=schemas.AIAdvisorResponse)
def query_ai_advisor(
    query_body: schemas.AIAdvisorQuery, 
    org_id: int = Query(1), 
    db: Session = Depends(get_db)
):
    """
    RAG-enabled multi-LLM advisor. Incorporates scoped database perimeters and scores into prompt contexts.
    """
    if not query_body.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")
        
    advice = get_ai_remediation_advice(query_body.query, db, organization_id=org_id)
    return advice

# --- AUTOMATED PDF REPORT ENDPOINTS ---

@app.get("/api/v1/report/pdf")
def get_pdf_report(org_id: int = Query(1), db: Session = Depends(get_db)):
    """
    Generates and streams a professional audit-grade PDF formatted for Swedish Regulators (MSB).
    """
    pdf_buffer = generate_ncsc_se_pdf(db, organization_id=org_id)
    filename = f"NIS2_Compliance_Audit_Org_{org_id}_{datetime.date.today().strftime('%Y_%m_%d')}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# --- SYSTEM CONFIG ENDPOINTS ---

@app.get("/api/v1/settings", response_model=schemas.SystemSettingsResponse)
def get_system_settings(org_id: int = Query(1), db: Session = Depends(get_db)):
    """
    Retrieves platform credentials and multi-LLM selections scoped per tenant.
    """
    settings = db.query(models.SystemSettings).filter(models.SystemSettings.organization_id == org_id).first()
    if not settings:
        settings = db.query(models.SystemSettings).filter(models.SystemSettings.id == 1).first()
        if not settings or settings.organization_id is not None:
            settings = models.SystemSettings(organization_id=org_id)
            db.add(settings)
            db.commit()
            db.refresh(settings)
    return settings

@app.put("/api/v1/settings", response_model=schemas.SystemSettingsResponse)
def update_system_settings(
    update_body: schemas.SystemSettingsUpdate, 
    org_id: int = Query(1), 
    db: Session = Depends(get_db)
):
    """
    Saves global configuration keys and triggers dynamic background scheduler adjustments.
    """
    settings = db.query(models.SystemSettings).filter(models.SystemSettings.organization_id == org_id).first()
    if not settings:
        settings = models.SystemSettings(organization_id=org_id)
        db.add(settings)
        db.commit()
        
    if update_body.scan_target is not None:
        settings.scan_target = update_body.scan_target
    if update_body.shodan_key is not None:
        settings.shodan_key = update_body.shodan_key
    if update_body.gemini_key is not None:
        settings.gemini_key = update_body.gemini_key
    
    # Multi-LLM provider & credential updates
    if update_body.llm_provider is not None:
        settings.llm_provider = update_body.llm_provider
    if update_body.openai_key is not None:
        settings.openai_key = update_body.openai_key
    if update_body.claude_key is not None:
        settings.claude_key = update_body.claude_key
        
    if update_body.slack_webhook is not None:
        settings.slack_webhook = update_body.slack_webhook
    if update_body.monitoring_active is not None:
        settings.monitoring_active = update_body.monitoring_active
        
    if update_body.scan_frequency is not None:
        settings.scan_frequency = update_body.scan_frequency
        # Reschedule APScheduler dynamically
        update_scheduler_interval(settings.scan_frequency)
        
    db.commit()
    db.refresh(settings)
    return settings

# --- DASHBOARD METRICS ENDPOINTS ---

@app.get("/api/v1/dashboard/stats", response_model=schemas.DashboardStats)
def get_dashboard_statistics(org_id: int = Query(1), db: Session = Depends(get_db)):
    """
    Gathers complex analytics scoped per tenant (overall compliance, critical assets, trends) to fuel frontend panels.
    """
    # 1. Total gaps count
    gaps = db.query(models.GapAnalysis).filter(models_or_fallback_filter(models.GapAnalysis, org_id)).all()
    avg_score = sum(g.score for g in gaps) / len(gaps) if gaps else 0.0
    critical_gaps_count = len([g for g in gaps if g.status == "Non-Compliant"])
    
    # 2. Assets counts
    assets = db.query(models.Asset).filter(models_or_fallback_filter(models.Asset, org_id)).all()
    scanned_count = len(assets)
    in_scope_count = len([a for a in assets if a.in_scope])
    critical_assets = db.query(models.Asset).filter(
        models.Asset.criticality == "Critical",
        models_or_fallback_filter(models.Asset, org_id)
    ).all()
    
    # 3. Gap breakdown by category (for donut charts)
    breakdown = {}
    for g in gaps:
        breakdown[g.category] = g.score
        
    # 4. History log trends scoped to tenant
    history = db.query(models.ComplianceHistory).filter(
        models_or_fallback_filter(models.ComplianceHistory, org_id)
    ).order_by(models.ComplianceHistory.recorded_at.asc()).all()
    
    return {
        "overall_compliance_score": round(avg_score, 1),
        "scanned_assets_count": scanned_count,
        "in_scope_assets_count": in_scope_count,
        "critical_gaps_count": critical_gaps_count,
        "gap_breakdown": breakdown,
        "history": history,
        "critical_assets": critical_assets
    }
