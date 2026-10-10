from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import get_settings
from .db import Base, SessionLocal, engine, get_db
from .models import Budget, Recommendation
from .schemas import CostRecordOut, SummaryOut
from .seed import seed_demo_data
from .services import costs_query, dashboard_aggregates, get_summary, sync_provider

BASE_DIR = Path(__file__).resolve().parent
settings = get_settings()
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        if settings.provider_mode == "mock":
            seed_demo_data(db)

    yield


app = FastAPI(title=settings.app_name, version="0.1.0", description="Open-source FinOps gateway with Odoo-ready normalized APIs", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/health")
def health():
    return {"status": "ok", "provider_mode": settings.provider_mode, "version": "0.1.0"}


@app.get("/api/v1/summary", response_model=SummaryOut)
def summary(days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    return get_summary(db, days)


@app.get("/api/v1/costs", response_model=list[CostRecordOut])
def costs(
    days: int = Query(30, ge=1, le=365),
    project: str | None = None,
    department: str | None = None,
    provider: str | None = None,
    db: Session = Depends(get_db),
):
    return costs_query(db, days, project, department, provider)


@app.get("/api/v1/budgets")
def budgets(db: Session = Depends(get_db)):
    return [
        {"project": b.project, "monthly_budget": b.monthly_budget, "currency": b.currency}
        for b in db.scalars(select(Budget).order_by(Budget.project)).all()
    ]


@app.get("/api/v1/recommendations")
def recommendations(db: Session = Depends(get_db)):
    return [
        {
            "id": r.id,
            "project": r.project,
            "resource": r.resource,
            "type": r.recommendation_type,
            "severity": r.severity,
            "estimated_monthly_saving": r.estimated_monthly_saving,
            "description": r.description,
            "status": r.status,
        }
        for r in db.scalars(select(Recommendation).order_by(Recommendation.estimated_monthly_saving.desc())).all()
    ]


@app.post("/api/v1/sync/provider")
async def provider_sync(db: Session = Depends(get_db)):
    try:
        return await sync_provider(db)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Provider sync failed: {exc}") from exc


@app.get("/api/v1/odoo/export")
def odoo_export(days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    """Normalized payload intentionally simple for an Odoo scheduled job."""
    return {
        "schema_version": "1.0",
        "summary": get_summary(db, days),
        "records": [CostRecordOut.model_validate(r).model_dump(mode="json") for r in costs_query(db, days)],
        "recommendations": recommendations(db),
    }


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, days: int = Query(30, ge=7, le=90), db: Session = Depends(get_db)):
    data = dashboard_aggregates(db, days)
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "summary": get_summary(db, days),
            "days": days,
            **data,
        },
    )
