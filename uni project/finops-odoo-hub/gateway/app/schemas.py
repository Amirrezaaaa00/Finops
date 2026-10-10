from datetime import date
from pydantic import BaseModel, ConfigDict


class CostRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    external_id: str
    usage_date: date
    provider: str
    account_id: str
    service: str
    category: str
    resource: str
    project: str
    department: str
    environment: str
    currency: str
    cost: float
    source: str


class SummaryOut(BaseModel):
    days: int
    total_cost: float
    currency: str
    forecast_30d: float
    active_projects: int
    active_services: int
    estimated_savings: float
    budget_total: float
    budget_utilization_pct: float
