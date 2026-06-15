app_name = "erpops"
app_title = "ErpOps"
app_publisher = "Operator"
app_description = "ErpOps custom app: Shopify API, Marketplace Alerts/Feeds"
app_email = "operator@example.com"
app_license = "MIT"
app_version = "0.0.1"
app_logo_url = "/assets/erpops/images/logo.png"
app_include_js = ["erpops.bundle.js"]

scheduler_events = {
    "all": [
        "erpops.erpops.scheduler.shopify_order_sync.sync_shopify_orders"
    ],
    "cron": {
        "*/15 * * * *": [
            "erpops.erpops.scheduler.alert_generator.generate_alerts"
        ],
    },
}

override_whitelisted_methods = {}

fixtures = [
    {"dt": "Custom DocType", "filters": [["module", "=", "ErpOps"]]},
    "Marketplace Alert",
    "Reorder Policy",
]

website_route_rules = [
    {
        "from_route": "/api/erpops/shopify_webhook",
        "to_route": "erpops.erpops.shopify.webhooks.handle_webhook",
    }
]

after_migrate = "erpops.erpops.app_setup.after_migrate"

jinja = {
    "methods": [],
    "filters": [],
}

doc_events = {
    "Shopify Setting": {
        "on_update": "erpops.erpops.shopify.doc_hooks.update_site_config"
    }
}
