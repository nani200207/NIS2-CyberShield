import datetime
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.app.database import SessionLocal
from backend.app.models import SystemSettings, ComplianceHistory, ScanLog, Organization
from backend.app.scanner import simulate_scan

scheduler = BackgroundScheduler()

def run_scheduled_scan():
    """
    In-process scheduler job. Resolves settings per organization and runs simulations.
    """
    db = SessionLocal()
    try:
        orgs = db.query(Organization).all()
        if not orgs:
            # Seed default organization
            default_org = Organization(id=1, name="Demo Corporation")
            db.add(default_org)
            db.commit()
            orgs = [default_org]
            
        for org in orgs:
            settings = db.query(SystemSettings).filter(SystemSettings.organization_id == org.id).first()
            if not settings:
                settings = db.query(SystemSettings).filter(SystemSettings.id == 1).first()
                if not settings:
                    continue
            
            if not settings.monitoring_active:
                continue
                
            print(f"[{datetime.datetime.now()}] Continuous Monitoring Rescan: Org '{org.name}' [ID: {org.id}]")
            simulate_scan(db, settings.scan_target, settings, organization_id=org.id)
            
    except Exception as e:
        print(f"Error in Scheduled Scan execution: {str(e)}")
    finally:
        db.close()

def init_scheduler():
    """
    Initializes pure in-process BackgroundScheduler.
    """
    db = SessionLocal()
    try:
        settings = db.query(SystemSettings).filter(SystemSettings.id == 1).first()
        if not settings:
            settings = SystemSettings(id=1)
            db.add(settings)
            db.commit()
            
        interval = settings.scan_frequency
        
        if not scheduler.running:
            scheduler.add_job(
                func=run_scheduled_scan,
                trigger=IntervalTrigger(minutes=interval),
                id='nis2_scheduled_scan',
                replace_existing=True
            )
            scheduler.start()
            print(f"In-Process Continuous Monitoring Agent active. Rescans mapped every {interval} minutes.")
    except Exception as e:
        print(f"Scheduler failed to initialize: {str(e)}")
    finally:
        db.close()

def update_scheduler_interval(minutes: int):
    """
    Allows adjusting sweep intervals dynamically from settings panels.
    """
    if scheduler.running:
        try:
            scheduler.reschedule_job(
                job_id='nis2_scheduled_scan',
                trigger=IntervalTrigger(minutes=minutes)
            )
            print(f"Continuous Monitoring rescheduled successfully to scan every {minutes} minutes.")
        except Exception as e:
            print(f"Failed to dynamically reschedule: {str(e)}")
