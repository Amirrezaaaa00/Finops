from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    finops_gateway_url = fields.Char(
        string="FinOps Gateway URL",
        config_parameter="finops_connector.gateway_url",
        default="http://finops-gateway:8000",
    )
