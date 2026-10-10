from app.providers.opencost import OpenCostProvider


def test_opencost_allocation_mapping():
    payload = {
        "code": 200,
        "data": [
            {
                "ai-platform": {
                    "properties": {
                        "cluster": "local-kind"
                    },
                    "window": {
                        "start": "2026-09-14T10:00:00Z",
                        "end": "2026-09-14T11:00:00Z"
                    },
                    "cpuCost": 0.10,
                    "ramCost": 0.05,
                    "pvCost": 0,
                    "networkCost": 0,
                    "totalCost": 0.15
                }
            }
        ]
    }

    rows = OpenCostProvider.map_response(
        payload
    )

    assert len(rows) == 2

    assert {
        row.project for row in rows
    } == {"AI Platform"}

    assert {
        row.service for row in rows
    } == {"CPU", "RAM"}

    assert round(
        sum(row.cost for row in rows), 2
    ) == 0.15

    assert all(
        row.provider == "OpenCost"
        for row in rows
    )