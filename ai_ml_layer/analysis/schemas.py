from typing import Optional
from pydantic import BaseModel, Field

class MetricValue(BaseModel):
    this_year: float
    last_year: float
    page: int
    label: str = ""
    confidence: str = "review"

class Metrics(BaseModel):
    basis: str = "Unspecified"
    unit: str = "Unit not identified"
    total_income: Optional[MetricValue] = None
    profit: Optional[MetricValue] = None
    total_assets: Optional[MetricValue] = None
    total_equity: Optional[MetricValue] = None
    income_growth_pct: Optional[float] = None
    profit_growth_pct: Optional[float] = None
    profit_margin_pct: Optional[float] = None
    equity_to_assets_pct: Optional[float] = None

class RiskFlag(BaseModel):
    type: str
    severity: str
    page: int
    evidence: str
    review_status: str = "human_review_required"
    reason: str = ""

class AnalysisReport(BaseModel):
    doc_id: str
    summary: str
    metrics: Metrics = Field(default_factory=Metrics)
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    risk_score: int = 0
    risk_score_label: str = "Disclosure signal index (0–100)"
    pages: int = 0
    extraction_warnings: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
