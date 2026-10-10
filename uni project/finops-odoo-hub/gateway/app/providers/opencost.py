from datetime import date, datetime
import hashlib

import httpx

from .base import CostProvider, NormalizedCost


PROJECTS = {
    "e-commerce": {
        "project": "E-Commerce",
        "department": "Digital",
    },
    "data-platform": {
        "project": "Data Platform",
        "department": "Data",
    },
    "crm": {
        "project": "CRM",
        "department": "Sales",
    },
    "ai-platform": {
        "project": "AI Platform",
        "department": "AI",
    },
}


COST_COMPONENTS = [
    ("cpuCost", "CPU", "Compute"),
    ("ramCost", "RAM", "Compute"),
    ("gpuCost", "GPU", "Compute"),
    ("pvCost", "Persistent Volume", "Storage"),
    ("networkCost", "Networking", "Network"),
    ("loadBalancerCost", "Load Balancer", "Network"),
    ("sharedCost", "Shared", "Other"),
    ("externalCost", "External", "Other"),
]


class OpenCostProvider(CostProvider):
    """OpenCost Kubernetes Allocation API adapter."""

    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @staticmethod
    def _parse_date(value: str | None) -> date:
        if not value:
            return date.today()

        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            ).date()
        except Exception:
            return date.today()

    @staticmethod
    def map_response(payload: dict) -> list[NormalizedCost]:
        rows: list[NormalizedCost] = []

        allocation_sets = (payload or {}).get("data") or []

        for allocation_set in allocation_sets:
            if not isinstance(allocation_set, dict):
                continue

            for namespace, item in allocation_set.items():
                # فقط چهار پروژه دانشگاهی خودمان وارد Gateway شوند.
                if namespace not in PROJECTS:
                    continue

                item = item or {}
                project_info = PROJECTS[namespace]

                window = item.get("window") or {}
                usage_date = OpenCostProvider._parse_date(
                    window.get("end") or window.get("start")
                )

                properties = item.get("properties") or {}
                cluster = str(properties.get("cluster") or "local-kind")

                component_total = 0.0

                for field_name, service, category in COST_COMPONENTS:
                    try:
                        cost = float(item.get(field_name) or 0.0)
                    except (TypeError, ValueError):
                        cost = 0.0

                    if cost <= 0:
                        continue

                    component_total += cost

                    raw_id = (
                        f"{usage_date}:{namespace}:"
                        f"{field_name}:{cluster}"
                    )

                    digest = hashlib.sha1(
                        raw_id.encode()
                    ).hexdigest()[:16]

                    rows.append(
                        NormalizedCost(
                            external_id=f"opencost:{digest}",
                            usage_date=usage_date,
                            provider="OpenCost",
                            account_id=cluster,
                            service=service,
                            category=category,
                            resource=namespace,
                            project=project_info["project"],
                            department=project_info["department"],
                            environment="local-kubernetes",
                            currency="USD",
                            cost=cost,
                            source="opencost-allocation",
                        )
                    )

                # اگر بخشی از totalCost در componentها نبود،
                # به عنوان Other ثبت می‌کنیم تا Total از بین نرود.
                try:
                    total_cost = float(item.get("totalCost") or 0.0)
                except (TypeError, ValueError):
                    total_cost = 0.0

                residual = max(total_cost - component_total, 0.0)

                if residual > 0:
                    raw_id = (
                        f"{usage_date}:{namespace}:"
                        f"other:{cluster}"
                    )

                    digest = hashlib.sha1(
                        raw_id.encode()
                    ).hexdigest()[:16]

                    rows.append(
                        NormalizedCost(
                            external_id=f"opencost:{digest}",
                            usage_date=usage_date,
                            provider="OpenCost",
                            account_id=cluster,
                            service="Other",
                            category="Other",
                            resource=namespace,
                            project=project_info["project"],
                            department=project_info["department"],
                            environment="local-kubernetes",
                            currency="USD",
                            cost=residual,
                            source="opencost-allocation",
                        )
                    )

        return rows

    async def fetch_costs(
        self,
        window: str,
    ) -> list[NormalizedCost]:

        async with httpx.AsyncClient(
            timeout=self.timeout
        ) as client:

            response = await client.get(
                f"{self.base_url}/allocation",
                params={
                    "window": window,
                    "aggregate": "namespace",
                    "resolution": "1m",
                },
            )

            response.raise_for_status()

            payload = response.json()

            if payload.get("code") != 200:
                raise RuntimeError(
                    f"OpenCost API returned: {payload}"
                )

            return self.map_response(payload)