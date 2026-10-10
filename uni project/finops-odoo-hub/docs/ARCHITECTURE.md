# Architecture

```text
Cloud Billing / Kubernetes
          |
          v
      OpenCost
   /cloudCost API
          |
          v
  FinOps Gateway (FastAPI)
  - normalization
  - mock mode
  - budget & savings
  - REST API
          |
          +---- Browser Dashboard
          |
          v
  Odoo Community Add-on
  finops_connector
  - scheduled sync
  - cost records
  - pivot / graph / list
```
