import logging
from datetime import timedelta
import requests
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class FinOpsCostRecord(models.Model):
    _name = "finops.cost.record"
    _description = "FinOps Cost Record"
    _order = "usage_date desc, cost desc"

    external_id = fields.Char(required=True, index=True, copy=False)
    usage_date = fields.Date(required=True, index=True)
    provider = fields.Char(required=True, index=True)
    account_id = fields.Char()
    service = fields.Char(required=True, index=True)
    category = fields.Char()
    resource = fields.Char()
    project_name = fields.Char(required=True, index=True)
    department = fields.Char(index=True)
    environment = fields.Char()
    currency_code = fields.Char(default="USD")
    cost = fields.Float(required=True, digits=(16, 4))
    source = fields.Char()
    project_id = fields.Many2one("project.project", string="Odoo Project", ondelete="set null")

    _external_id_unique = models.Constraint("UNIQUE(external_id)", "External cost record must be unique.")

    @api.model
    def _gateway_url(self):
        return self.env["ir.config_parameter"].sudo().get_param("finops_connector.gateway_url", "http://finops-gateway:8000").rstrip("/")

    @api.model
    def sync_from_gateway(self, days=30):
        url = f"{self._gateway_url()}/api/v1/odoo/export"
        try:
            response = requests.get(url, params={"days": days}, timeout=25)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            _logger.exception("FinOps gateway synchronization failed")
            raise UserError(f"FinOps gateway connection failed: {exc}") from exc

        created = updated = 0
        Project = self.env["project.project"].sudo()
        for item in payload.get("records", []):
            project_name = item.get("project") or "Unallocated"
            project = Project.search([("name", "=", project_name)], limit=1)
            vals = {
                "external_id": item["external_id"],
                "usage_date": item["usage_date"],
                "provider": item.get("provider") or "Unknown",
                "account_id": item.get("account_id") or "",
                "service": item.get("service") or "Unknown",
                "category": item.get("category") or "Other",
                "resource": item.get("resource") or "",
                "project_name": project_name,
                "department": item.get("department") or "Unallocated",
                "environment": item.get("environment") or "unknown",
                "currency_code": item.get("currency") or "USD",
                "cost": float(item.get("cost") or 0),
                "source": item.get("source") or "gateway",
                "project_id": project.id if project else False,
            }
            record = self.search([("external_id", "=", vals["external_id"])], limit=1)
            if record:
                record.write(vals)
                updated += 1
            else:
                self.create(vals)
                created += 1
        return {"created": created, "updated": updated, "received": len(payload.get("records", []))}

    @api.model
    def _cron_sync_from_gateway(self):
        return self.sync_from_gateway(days=30)

    def action_sync_now(self):
        result = self.sync_from_gateway(days=30)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "FinOps Sync",
                "message": f"Created: {result['created']} | Updated: {result['updated']}",
                "type": "success",
                "sticky": False,
            },
        }
