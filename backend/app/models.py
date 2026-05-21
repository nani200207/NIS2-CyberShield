import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text
from backend.app.database import Base

class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    ip = Column(String(50), unique=True, index=True, nullable=False)
    hostname = Column(String(255), nullable=True)
    mac_address = Column(String(50), nullable=True)
    ports = Column(String(255), nullable=True)  # Comma-separated list like "22,80,443"
    os = Column(String(100), nullable=True)
    services = Column(Text, nullable=True)  # JSON string of open services
    shodan_data = Column(Text, nullable=True)  # JSON string containing Shodan API details
    in_scope = Column(Boolean, default=False)
    scope_sector = Column(String(100), nullable=True)  # e.g., "Energy", "Digital Infrastructure"
    criticality = Column(String(50), default="Medium")  # Critical, High, Medium, Low
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)

class GapAnalysis(Base):
    __tablename__ = "gap_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(String(50), unique=True, index=True, nullable=False) # e.g., "Art 21.2a"
    category = Column(String(255), nullable=False)
    control_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    score = Column(Integer, default=0)  # 0 to 100
    status = Column(String(50), default="Non-Compliant")  # Compliant, Partial, Non-Compliant
    remediation_steps = Column(Text, nullable=True)
    comments = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class ComplianceHistory(Base):
    __tablename__ = "compliance_history"
    
    id = Column(Integer, primary_key=True, index=True)
    score = Column(Float, nullable=False)
    scanned_assets = Column(Integer, nullable=False)
    critical_gaps = Column(Integer, nullable=False)
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)

class ScanLog(Base):
    __tablename__ = "scan_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    level = Column(String(50), default="INFO")  # INFO, WARNING, ERROR, SUCCESS, TERMINAL
    message = Column(Text, nullable=False)

class SystemSettings(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, default=1)
    scan_target = Column(String(255), default="192.168.1.0/24")
    scan_frequency = Column(Integer, default=60)  # in minutes
    shodan_key = Column(String(255), default="")
    gemini_key = Column(String(255), default="")
    slack_webhook = Column(String(255), default="")
    monitoring_active = Column(Boolean, default=True)
