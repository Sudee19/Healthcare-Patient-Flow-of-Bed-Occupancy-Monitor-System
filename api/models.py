"""
Pydantic models for API request/response schemas.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class WardStatus(BaseModel):
    ward_id: str
    ward_name: str
    occupied_beds: int
    total_beds: int
    occupancy_percent: float
    status: str  # normal, elevated, warning, critical
    trend: Optional[str] = "stable"
    last_hour_occupancy_percent: Optional[float] = None
    updated_at: Optional[str] = None

class WardHourly(BaseModel):
    ward_id: str
    ward_name: str
    snapshot_hour: str
    occupied_beds: int
    total_beds: int
    occupancy_percent: float
    admits_count: Optional[int] = 0
    discharges_count: Optional[int] = 0

class WardBaseline(BaseModel):
    ward_id: str
    ward_name: str
    hour_of_day: int
    baseline_avg_occupancy: float
    baseline_std_occupancy: Optional[float] = 0.0
    sample_count: Optional[int] = 0

class SLABreach(BaseModel):
    id: int
    ward_id: str
    ward_name: str
    breach_start_time: str
    breach_end_time: Optional[str] = None
    consecutive_hours: Optional[float] = 0
    peak_occupancy_percent: Optional[float] = None
    current_occupancy_percent: Optional[float] = None
    status: str
    llm_explanation: Optional[str] = None
    llm_confidence: Optional[str] = None
    resolved_at: Optional[str] = None

class AnomalyFlag(BaseModel):
    id: int
    ward_id: str
    ward_name: str
    detection_time: str
    hour_of_day: int
    z_score: float
    is_anomaly: bool
    baseline_mean: float
    baseline_std: float
    current_count: int
    threshold_used: Optional[float] = 2.5

class AlertEvent(BaseModel):
    id: Optional[int] = None
    alert_type: str
    ward_id: str
    ward_name: str
    severity: str
    occupancy_percent: Optional[float] = None
    message: Optional[str] = None
    llm_explanation: Optional[str] = None
    created_at: Optional[str] = None
