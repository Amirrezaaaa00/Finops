from datetime import date, timedelta
import hashlib
import math
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .models import Budget, CostRecord, Recommendation


PROJECTS = [
    ("E-Commerce", "Digital", 900.0),
    ("Data Platform", "Data", 1150.0),
    ("CRM", "Sales", 650.0),
    ("AI Platform", "AI", 800.0),
]
SERVICES = [
    ("Compute", "Compute", 1.00),
    ("Database", "Database", 0.72),
    ("Object Storage", "Storage", 0.34),
    ("Networking", "Network", 0.22),
]


def _stable_noise(key: str) -> float:
    h = hashlib.sha256(key.encode()).hexdigest()
    n = int(h[:8], 16) / 0xFFFFFFFF
    return 0.84 + n * 0.34


def seed_demo_data(db: Session, days: int = 90) -> None:
    count = db.scalar(select(func.count()).select_from(CostRecord)) or 0
    if count:
        return

    today = date.today()
    for project, department, budget in PROJECTS:
        db.add(Budget(project=project, monthly_budget=budget, currency="USD"))

    for offset in range(days):
        d = today - timedelta(days=offset)
        weekly = 1.0 + 0.08 * math.sin(offset / 7 * math.pi * 2)
        growth = 1.0 + (days - offset) / days * 0.11
        for p_idx, (project, department, _) in enumerate(PROJECTS):
            project_factor = [1.0, 1.24, 0.68, 1.10][p_idx]
            for s_idx, (service, category, svc_factor) in enumerate(SERVICES):
                noise = _stable_noise(f"{d}-{project}-{service}")
                base = 7.5 * project_factor * svc_factor * weekly * growth * noise
                # create a controlled anomaly in the last week for Data Platform / Compute
                if offset <= 6 and project == "Data Platform" and service == "Compute":
                    base *= 1.42
                resource = f"{project.lower().replace(' ', '-')}-{service.lower().replace(' ', '-')}-{s_idx+1}"
                external_id = f"mock:{d}:{project}:{service}"
                db.add(CostRecord(
                    external_id=external_id,
                    usage_date=d,
                    provider="OpenCost-Mock",
                    account_id="demo-account",
                    service=service,
                    category=category,
                    resource=resource,
                    project=project,
                    department=department,
                    environment="production" if project != "CRM" else "staging",
                    currency="USD",
                    cost=round(base, 4),
                    source="mock",
                ))

    recs = [
        ("Data Platform", "data-platform-compute-1", "Rightsizing", "high", 128.0, "کاهش اندازه نمونه محاسباتی با توجه به الگوی مصرف مشاهده‌شده."),
        ("E-Commerce", "e-commerce-compute-1", "Schedule", "medium", 64.0, "خاموش‌کردن منابع غیرتولیدی خارج از ساعات کاری."),
        ("CRM", "crm-object-storage-3", "Storage lifecycle", "low", 28.0, "انتقال داده‌های کم‌مصرف به کلاس ذخیره‌سازی ارزان‌تر."),
        ("Data Platform", "data-platform-database-2", "Commitment review", "medium", 75.0, "بررسی الگوی مصرف پایدار برای استفاده از تخفیف تعهدی."),
    ]
    for project, resource, rtype, severity, saving, description in recs:
        db.add(Recommendation(
            project=project,
            resource=resource,
            recommendation_type=rtype,
            severity=severity,
            estimated_monthly_saving=saving,
            description=description,
            status="open",
        ))
    db.commit()
