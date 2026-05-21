import requests
import datetime
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.app.database import SessionLocal
from backend.app.models import SystemSettings, ComplianceHistory, ScanLog
from backend.app.scanner import simulate_scan, run_real_scan

scheduler = BackgroundScheduler()

def get_db_context():
    """Helper to open db session for scheduler thread."""
    return SessionLocal()

def run_scheduled_scan():
    """
    Main job that runs periodically. Resolves the database config,
    executes the scan, and checks if score dropped to trigger Slack alerts.
    """
    db = get_db_context()
    try:
        settings = db.query(SystemSettings).first()
        if not settings or not settings.monitoring_active:
            print("Monitoring is currently inactive or not configured.")
            return
            
        print(f"[{datetime.datetime.now()}] Continuous Monitoring Agent triggering re-scan...")
        
        # 1. Capture score BEFORE scan
        prev_history = db.query(ComplianceHistory).order_by(ComplianceHistory.recorded_at.desc()).first()
        prev_score = prev_history.score if prev_history else 50.0
        
        # 2. Run Scanner (Simulation or Real)
        # For background scheduled tasks, we simulate to populate and update data,
        # unless they have specific socket triggers
        simulate_scan(db, settings.scan_target, settings)
        
        # 3. Capture score AFTER scan
        db.expire_all() # Ensure SQLAlchemy updates cache
        new_history = db.query(ComplianceHistory).order_by(ComplianceHistory.recorded_at.desc()).first()
        new_score = new_history.score if new_history else 50.0
        
        print(f"Compliance score evaluation: Previous: {prev_score}% | Current: {new_score}%")
        
        # 4. Check if compliance dropped
        if new_score < prev_score:
            message = f"🚨 *[NIS2 CyberShield Alert]* Compliance score has dropped from {prev_score}% to {new_score}%!\n" \
                      f"Detected new exposure or changes on target subnet *{settings.scan_target}*.\n" \
                      f"Please visit the Compliance Dashboard to execute remediation."
            trigger_slack_notification(settings.slack_webhook, message)
            
        # Also alert if critical gaps exist
        critical_gaps_count = new_history.critical_gaps if new_history else 0
        if critical_gaps_count > 0 and prev_score != new_score:
            alert_msg = f"⚠ *[NIS2 CyberShield Alert]* Discovered {critical_gaps_count} critical Non-Compliant Article 21 requirements during automated monitoring."
            trigger_slack_notification(settings.slack_webhook, alert_msg)
            
    except Exception as e:
        print(f"Error in Scheduled Scan execution: {str(e)}")
    finally:
        db.close()

def trigger_slack_notification(webhook_url: str, message: str):
    """Sends JSON webhook to Slack/Discord."""
    if not webhook_url:
        print(f"Slack webhook not configured. Notification message: {message}")
        return
        
    try:
        payload = {"text": message}
        res = requests.post(webhook_url, json=payload, timeout=5)
        if res.status_code == 200:
            print("Successfully sent alert notification to Slack!")
        else:
            print(f"Slack webhook endpoint returned error {res.status_code}: {res.text}")
    except Exception as e:
        print(f"Failed to transmit Slack alert: {str(e)}")

def init_scheduler():
    """
    Initializes the scheduler thread. Reads frequency from Settings database.
    """
    db = get_db_context()
    try:
        settings = db.query(SystemSettings).first()
        if not settings:
            settings = SystemSettings()
            db.add(settings)
            db.commit()
            
        # Defaults to 60 minutes
        interval = settings.scan_frequency
        
        # Start background job
        if not scheduler.running:
            scheduler.add_job(
                func=run_scheduled_scan,
                trigger=IntervalTrigger(minutes=interval),
                id='nis2_scheduled_scan',
                replace_existing=True
            )
            scheduler.start()
            print(f"Continuous Monitoring Agent initialized. Subnet Rescan scheduled every {interval} minutes.")
    except Exception as e:
        print(f"Scheduler failed to initialize: {str(e)}")
    finally:
        db.close()

def update_scheduler_interval(minutes: int):
    """
    Allows the user to adjust scanning frequency dynamically from the dashboard settings.
    """
    if scheduler.running:
        try:
            scheduler.reschedule_job(
                job_id='nis2_scheduled_scan',
                trigger=IntervalTrigger(minutes=minutes)
            )
            print(f"Continuous Monitoring Agent successfully rescheduled scanning to every {minutes} minutes.")
        except Exception as e:
            print(f"Failed rescheduling scheduled scan: {str(e)}")
