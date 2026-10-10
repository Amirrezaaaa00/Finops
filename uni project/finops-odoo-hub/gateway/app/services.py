from datetime import date, timedelta
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session
from .config import get_settings
from .models import Budget, CostRecord, Recommendation
from .providers.opencost import OpenCostProvider


def date_cutoff(days: int) -> date:
    return date.today() - timedelta(days=max(days - 1, 0))


def get_summary(db: Session, days: int = 30) -> dict:
    cutoff = date_cutoff(days)
    total = db.scalar(select(func.coalesce(func.sum(CostRecord.cost), 0.0)).where(CostRecord.usage_date >= cutoff)) or 0.0
    projects = db.scalar(select(func.count(func.distinct(CostRecord.project))).where(CostRecord.usage_date >= cutoff)) or 0
    services = db.scalar(select(func.count(func.distinct(CostRecord.service))).where(CostRecord.usage_date >= cutoff)) or 0
    savings = db.scalar(select(func.coalesce(func.sum(Recommendation.estimated_monthly_saving), 0.0)).where(Recommendation.status == "open")) or 0.0
    budget_total = db.scalar(select(func.coalesce(func.sum(Budget.monthly_budget), 0.0))) or 0.0
    forecast = (float(total) / max(days, 1)) * 30
    util = forecast / budget_total * 100 if budget_total else 0.0
    return {
        "days": days,
        "total_cost": round(float(total), 2),
        "currency": get_settings().currency,
        "forecast_30d": round(float(forecast), 2),
        "active_projects": int(projects),
        "active_services": int(services),
        "estimated_savings": round(float(savings), 2),
        "budget_total": round(float(budget_total), 2),
        "budget_utilization_pct": round(float(util), 1),
    }


def costs_query(db: Session, days: int = 30, project: str | None = None, department: str | None = None, provider: str | None = None):
    stmt = select(CostRecord).where(CostRecord.usage_date >= date_cutoff(days))
    if project:
        stmt = stmt.where(CostRecord.project == project)
    if department:
        stmt = stmt.where(CostRecord.department == department)
    if provider:
        stmt = stmt.where(CostRecord.provider == provider)
    return db.scalars(stmt.order_by(CostRecord.usage_date.desc(), CostRecord.cost.desc())).all()


def dashboard_aggregates(db: Session, days: int = 30) -> dict:
    cutoff = date_cutoff(days)
    by_project = db.execute(
        select(CostRecord.project, func.sum(CostRecord.cost)).where(CostRecord.usage_date >= cutoff).group_by(CostRecord.project).order_by(func.sum(CostRecord.cost).desc())
    ).all()
    by_service = db.execute(
        select(CostRecord.service, func.sum(CostRecord.cost)).where(CostRecord.usage_date >= cutoff).group_by(CostRecord.service).order_by(func.sum(CostRecord.cost).desc())
    ).all()
    trend = db.execute(
        select(CostRecord.usage_date, func.sum(CostRecord.cost)).where(CostRecord.usage_date >= cutoff).group_by(CostRecord.usage_date).order_by(CostRecord.usage_date)
    ).all()
    budgets = {b.project: b.monthly_budget for b in db.scalars(select(Budget)).all()}
    recs = db.scalars(select(Recommendation).order_by(Recommendation.estimated_monthly_saving.desc())).all()
    return {
        "by_project": [(x, round(float(y), 2)) for x, y in by_project],
        "by_service": [(x, round(float(y), 2)) for x, y in by_service],
        "trend": [(x.isoformat(), round(float(y), 2)) for x, y in trend],
        "budgets": budgets,
        "recommendations": recs,
    }


async def sync_provider(db: Session) -> dict:
    settings = get_settings()

    if settings.provider_mode != "opencost":
        return {
            "provider": settings.provider_mode,
            "created": 0,
            "updated": 0,
            "message": "در حالت mock همگام‌سازی خارجی غیرفعال است.",
        }

    provider = OpenCostProvider(
        settings.opencost_base_url
    )

    rows = await provider.fetch_costs(
        settings.opencost_window
    )

    created = 0
    updated = 0

    for row in rows:
        record = db.scalar(
            select(CostRecord).where(
                CostRecord.external_id
                == row.external_id
            )
        )

        if record:
            for field_name, value in row.__dict__.items():
                setattr(record, field_name, value)

            updated += 1

        else:
            db.add(
                CostRecord(**row.__dict__)
            )
            created += 1

    db.commit()

    return {
        "provider": "opencost",
        "created": created,
        "updated": updated,
        "received": len(rows),
    }