# FinOps Odoo Hub — نمونه دانشگاهی متن‌باز

این پروژه یک نمونه عملی FinOps است که سه بخش دارد:

1. **FinOps Gateway**: سرویس FastAPI برای نرمال‌سازی داده هزینه و ارائه API و داشبورد.
2. **OpenCost Adapter**: اتصال اختیاری به API متن‌باز OpenCost. حالت پیش‌فرض پروژه `mock` است تا بدون Cloud و Kubernetes قابل نمایش باشد.
3. **Odoo Community Add-on**: ماژول `finops_connector` برای ورود هزینه‌ها به Odoo و نمایش List/Pivot/Graph.

## اجرای سریع بدون Docker و بدون Odoo

```bash
cd gateway
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

سپس:
- Dashboard: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs
- Odoo normalized payload: http://127.0.0.1:8000/api/v1/odoo/export

## اجرای کامل با Docker Compose

نیازمند Docker Desktop یا Docker Engine است:

```bash
cp .env.example .env
docker compose up -d --build
```

سپس:
- Gateway: http://localhost:8000
- Odoo: http://localhost:8069

پس از ساخت دیتابیس Odoo، Apps را باز کنید، لیست برنامه‌ها را Update کنید و **FinOps Connector** را نصب کنید.

## اتصال واقعی OpenCost

در `.env`:

```env
FINOPS_PROVIDER_MODE=opencost
FINOPS_OPENCOST_BASE_URL=http://host.docker.internal:9003
FINOPS_OPENCOST_WINDOW=30d
```

Gateway از `/cloudCost` داده را می‌خواند و آن را به مدل ثابت پروژه تبدیل می‌کند.

## تست

```bash
cd gateway
pytest -q
```

## نکته دانشگاهی

داده‌های پیش‌فرض ماکت هستند و برای ارائه، آموزش و تست طراحی شده‌اند. پس از راه‌اندازی OpenCost می‌توان بدون تغییر Odoo، فقط Provider را از `mock` به `opencost` تغییر داد.
