from typing import Optional
from pydantic import BaseModel


class Metrics(BaseModel):
    revenue: Optional[float] = None
    net_income: Optional[float] = None
    total_debt: Optional[float] = None
    total_equity: Optional[float] = None


class AnalysisReport(BaseModel):
    summary: str
    metrics: Metrics = Metrics()
