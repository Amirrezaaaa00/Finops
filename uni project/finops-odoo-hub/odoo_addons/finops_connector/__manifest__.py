{
    "name": "FinOps Connector",
    "version": "19.0.1.0.0",
    "summary": "Open-source FinOps cost data integration for Odoo Community",
    "category": "Accounting/Accounting",
    "author": "University FinOps Project",
    "license": "LGPL-3",
    "depends": ["base", "project"],
    "external_dependencies": {"python": ["requests"]},
    "data": [
        "security/ir.model.access.csv",
        "views/finops_cost_views.xml",
        "views/res_config_settings_views.xml",
        "data/ir_cron.xml",
    ],
    "application": True,
    "installable": True,
}
