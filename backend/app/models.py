import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Cascade deletes to all related models
    assets = relationship("Asset", back_populates="organization", cascade="all, delete-orphan")
    gaps = relationship("GapAnalysis", back_populates="organization", cascade="all, delete-orphan")
    history = relationship("ComplianceHistory", back_populates="organization", cascade="all, delete-orphan")
    settings = relationship("SystemSettings", back_populates="organization", cascade="all, delete-orphan")
    tasks = relationship("RemediationTask", back_populates="organization", cascade="all, delete-orphan")
    scan_logs = relationship("ScanLog", back_populates="organization", cascade="all, delete-orphan")

class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
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
    dynamic_risk_score = Column(Float, default=0.0)  # Computed dynamic risk index
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)

    organization = relationship("Organization", back_populates="assets")

class GapAnalysis(Base):
    __tablename__ = "gap_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    article_id = Column(String(50), index=True, nullable=False) # e.g., "Art 21.2a"
    category = Column(String(255), nullable=False)
    control_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    score = Column(Integer, default=0)  # 0 to 100
    status = Column(String(50), default="Non-Compliant")  # Compliant, Partial, Non-Compliant
    remediation_steps = Column(Text, nullable=True)
    comments = Column(Text, nullable=True)
    evidence_file_path = Column(String(255), nullable=True)  # File path to uploaded auditor evidence
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    organization = relationship("Organization", back_populates="gaps")
    tasks = relationship("RemediationTask", back_populates="gap", cascade="all, delete-orphan")

class ComplianceHistory(Base):
    __tablename__ = "compliance_history"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    score = Column(Float, nullable=False)
    scanned_assets = Column(Integer, nullable=False)
    critical_gaps = Column(Integer, nullable=False)
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)

    organization = relationship("Organization", back_populates="history")

class ScanLog(Base):
    __tablename__ = "scan_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    level = Column(String(50), default="INFO")  # INFO, WARNING, ERROR, SUCCESS, TERMINAL
    message = Column(Text, nullable=False)

    organization = relationship("Organization", back_populates="scan_logs")

class SystemSettings(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, default=1)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    scan_target = Column(String(255), default="192.168.1.0/24")
    scan_frequency = Column(Integer, default=60)  # in minutes
    shodan_key = Column(String(255), default="")
    gemini_key = Column(String(255), default="")
    
    # Multi-LLM keys
    llm_provider = Column(String(50), default="Google Gemini")  # Google Gemini, OpenAI GPT-4, Anthropic Claude
    openai_key = Column(String(255), default="")
    claude_key = Column(String(255), default="")
    
    slack_webhook = Column(String(255), default="")
    monitoring_active = Column(Boolean, default=True)

    organization = relationship("Organization", back_populates="settings")

class RemediationTask(Base):
    __tablename__ = "remediation_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    gap_id = Column(String(50), ForeignKey("gap_analysis.article_id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    assignee = Column(String(255), nullable=True)
    due_date = Column(DateTime, nullable=True)
    status = Column(String(50), default="Open")  # Open, In Progress, Done
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    organization = relationship("Organization", back_populates="tasks")
    gap = relationship("GapAnalysis", foreign_keys=[gap_id], primaryjoin="RemediationTask.gap_id == GapAnalysis.article_id", back_populates="tasks")
