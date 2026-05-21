from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Asset schemas
class AssetBase(BaseModel):
    ip: str
    hostname: Optional[str] = None
    mac_address: Optional[str] = None
    ports: Optional[str] = None
    os: Optional[str] = None
    services: Optional[str] = None
    shodan_data: Optional[str] = None
    in_scope: bool = False
    scope_sector: Optional[str] = None
    criticality: str = "Medium"

class AssetCreate(AssetBase):
    pass

class AssetResponse(AssetBase):
    id: int
    detected_at: datetime

    class Config:
        from_attributes = True

# Gap Analysis schemas
class GapAnalysisBase(BaseModel):
    article_id: str
    category: str
    control_name: str
    description: str
    score: int
    status: str
    remediation_steps: Optional[str] = None
    comments: Optional[str] = None

class GapAnalysisUpdate(BaseModel):
    score: Optional[int] = None
    status: Optional[str] = None
    comments: Optional[str] = None
    remediation_steps: Optional[str] = None

class GapAnalysisResponse(GapAnalysisBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True

# Compliance History schemas
class ComplianceHistoryResponse(BaseModel):
    id: int
    score: float
    scanned_assets: int
    critical_gaps: int
    recorded_at: datetime

    class Config:
        from_attributes = True

# Scan Log schemas
class ScanLogResponse(BaseModel):
    id: int
    timestamp: datetime
    level: str
    message: str

    class Config:
        from_attributes = True

# System Settings schemas
class SystemSettingsBase(BaseModel):
    scan_target: str
    scan_frequency: int
    shodan_key: str
    gemini_key: str
    slack_webhook: str
    monitoring_active: bool

class SystemSettingsUpdate(BaseModel):
    scan_target: Optional[str] = None
    scan_frequency: Optional[int] = None
    shodan_key: Optional[str] = None
    gemini_key: Optional[str] = None
    slack_webhook: Optional[str] = None
    monitoring_active: Optional[bool] = None

class SystemSettingsResponse(SystemSettingsBase):
    id: int

    class Config:
        from_attributes = True

# AI Chat schemas
class AIAdvisorQuery(BaseModel):
    query: str
    category_filter: Optional[str] = None

class AIAdvisorResponse(BaseModel):
    response: str
    sources: List[str] = []

# Dashboard Stats schemas
class DashboardStats(BaseModel):
    overall_compliance_score: float
    scanned_assets_count: int
    in_scope_assets_count: int
    critical_gaps_count: int
    gap_breakdown: Dict[str, float]
    history: List[ComplianceHistoryResponse]
    critical_assets: List[AssetResponse]
