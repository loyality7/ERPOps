import frappe

def after_migrate():
    create_custom_fields()
    ensure_module_def()
    setup_workspace()
    hide_standard_workspaces()
    setup_shopify_integration()

def create_custom_fields():
    """Programmatically create custom fields required for Shopify integration."""
    custom_fields = {
        "Sales Order": [
            {
                "fieldname": "custom_shopify_order_id",
                "label": "Shopify Order ID",
                "fieldtype": "Data",
                "insert_after": "naming_series"
            },
            {
                "fieldname": "custom_channel",
                "label": "Channel",
                "fieldtype": "Data",
                "insert_after": "custom_shopify_order_id"
            },
            {
                "fieldname": "custom_payment_status",
                "label": "Payment Status",
                "fieldtype": "Data",
                "insert_after": "custom_channel"
            }
        ],
        "Delivery Note": [
            {
                "fieldname": "custom_shopify_fulfillment_id",
                "label": "Shopify Fulfillment ID",
                "fieldtype": "Data",
                "insert_after": "naming_series"
            }
        ]
    }

    for dt, fields in custom_fields.items():
        for f in fields:
            # Document key is formatted as "DocType-fieldname"
            doc_name = f"{dt}-{f['fieldname']}"
            if not frappe.db.exists("Custom Field", doc_name):
                df = frappe.new_doc("Custom Field")
                df.dt = dt
                df.fieldname = f["fieldname"]
                df.label = f["label"]
                df.fieldtype = f["fieldtype"]
                df.insert_after = f["insert_after"]
                df.insert(ignore_permissions=True)
                print(f"Created Custom Field: {dt} -> {f['fieldname']}")
    frappe.db.commit()

def ensure_module_def():
    """Ensure that the ErpOps Module Def exists in the database."""
    if not frappe.db.exists("Module Def", "ErpOps"):
        frappe.get_doc({
            "doctype": "Module Def",
            "module_name": "ErpOps",
            "app_name": "erpops"
        }).insert(ignore_permissions=True)
        frappe.db.commit()


def setup_workspace():
    """Create or update ErpOps custom workspace linking the dashboard page."""
    import os
    from frappe.modules.import_file import import_file_by_path
    
    app_path = frappe.get_app_path("erpops")
    
    # Manually import custom doctypes and dashboard page first to satisfy LinkValidation
    doctype_names = ["Marketplace Alert", "Reorder Policy"]
    for dt in doctype_names:
        folder_name = dt.lower().replace(" ", "_")
        path = os.path.join(app_path, "doctype", folder_name, f"{folder_name}.json")
        if os.path.exists(path):
            import_file_by_path(path, force=True)
            
    page_path = os.path.join(app_path, "page", "erpops_dashboard", "erpops_dashboard.json")
    if os.path.exists(page_path):
        import_file_by_path(page_path, force=True)

    workspace_name = "ErpOps"
    import json
    
    if frappe.db.exists("Workspace", workspace_name):
        doc = frappe.get_doc("Workspace", workspace_name)
    else:
        doc = frappe.new_doc("Workspace")
        doc.name = workspace_name
        doc.label = workspace_name
        doc.title = workspace_name
        doc.icon = "dashboard"
        doc.public = 1
        doc.module = "ErpOps"
        
    doc.is_hidden = 0
    doc.sequence_id = 1
    
    # Rebuild the links child table
    doc.links = []
    doc.append("links", {
        "type": "Card Break",
        "label": "ErpOps"
    })
    doc.append("links", {
        "link_type": "Page",
        "link_to": "erpops_dashboard",
        "label": "Operational Dashboard",
        "type": "Link",
        "icon": "dashboard",
        "is_query_report": 0
    })
    
    doc.append("links", {
        "link_type": "DocType",
        "link_to": "Marketplace Alert",
        "label": "Marketplace Alerts",
        "type": "Link",
        "icon": "alert",
        "is_query_report": 0
    })
    
    doc.append("links", {
        "link_type": "DocType",
        "link_to": "Reorder Policy",
        "label": "Reorder Policies",
        "type": "Link",
        "icon": "settings",
        "is_query_report": 0
    })

    doc.append("links", {
        "link_type": "DocType",
        "link_to": "Shopify Setting",
        "label": "Shopify Integration Settings",
        "type": "Link",
        "icon": "share",
        "is_query_report": 0
    })

    # Rebuild the shortcuts child table
    doc.shortcuts = []
    doc.append("shortcuts", {
        "type": "Page",
        "link_to": "erpops_dashboard",
        "label": "Operational Dashboard",
        "icon": "dashboard",
        "color": "Green"
    })
    doc.append("shortcuts", {
        "type": "DocType",
        "link_to": "Marketplace Alert",
        "label": "Marketplace Alerts",
        "icon": "alert",
        "color": "Red"
    })
    doc.append("shortcuts", {
        "type": "DocType",
        "link_to": "Reorder Policy",
        "label": "Reorder Policies",
        "icon": "settings",
        "color": "Blue"
    })

    # Set content JSON for native v15 grid layout
    doc.content = json.dumps([
        {"id": "eo_h1", "type": "header", "data": {"text": "<span class=\"h3\"><b>ErpOps Integration Center</b></span>", "col": 12}},
        {"id": "eo_sc1", "type": "shortcut", "data": {"shortcut_name": "Operational Dashboard", "label": "Operational Dashboard", "icon": "dashboard", "color": "Green", "col": 4}},
        {"id": "eo_sc2", "type": "shortcut", "data": {"shortcut_name": "Marketplace Alerts", "label": "Marketplace Alerts", "icon": "alert", "color": "Red", "col": 4}},
        {"id": "eo_sc3", "type": "shortcut", "data": {"shortcut_name": "Reorder Policies", "label": "Reorder Policies", "icon": "settings", "color": "Blue", "col": 4}},
        {"id": "eo_sp1", "type": "spacer", "data": {"col": 12}},
        {"id": "eo_h2", "type": "header", "data": {"text": "<span class=\"h4\"><b>Operations Database</b></span>", "col": 12}},
        {"id": "eo_c1", "type": "card", "data": {"card_name": "ErpOps", "col": 4}}
    ])
    
    doc.save(ignore_permissions=True)
    frappe.db.commit()

def hide_standard_workspaces():
    """Hide standard workspaces to declutter the sidebar."""
    workspaces_to_hide = [
        "Accounting", "HR", "Buying", "Selling", "Stock", "Assets", "CRM", 
        "Build", "Projects", "Support", "Manufacturing", "Quality", "Agriculture", 
        "Settings", "Tools", "Integrations", "Users", "Website", "Loans", "Retail",
        "Workspaces", "Education", "Healthcare", "Data Import and Export", "Desk", 
        "Utilities"
    ]
    for name in workspaces_to_hide:
        if frappe.db.exists("Workspace", name):
            frappe.db.set_value("Workspace", name, "is_hidden", 1)
            
    # Make sure ErpOps is visible
    if frappe.db.exists("Workspace", "ErpOps"):
        frappe.db.set_value("Workspace", "ErpOps", "is_hidden", 0)
        
    frappe.db.commit()


def setup_shopify_integration():
    """Dynamically set up Shopify Setting and site_config during migrations if env vars are present."""
    import os
    import urllib.request
    import urllib.parse
    import json
    
    client_id = os.environ.get("SHOPIFY_CLIENT_ID") or getattr(frappe.conf, "shopify_client_id", None)
    client_secret = os.environ.get("SHOPIFY_CLIENT_SECRET") or getattr(frappe.conf, "shopify_client_secret", None)
    shop = os.environ.get("SHOPIFY_SHOP") or getattr(frappe.conf, "shopify_domain", "ddfhhg-ae.myshopify.com")
    
    if not client_id or not client_secret:
        print("Automatic Shopify setup: Missing client_id or client_secret.")
        return
        
    # Clean shop domain
    shop = shop.replace("https://", "").replace("http://", "").rstrip("/")
    if not shop.endswith(".myshopify.com"):
        shop = f"{shop}.myshopify.com"
        
    print(f"Automatic Shopify setup: Exchanging credentials for shop '{shop}'...")
    
    # 1. Fetch access token from Shopify
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }).encode()

    req = urllib.request.Request(
        f"https://{shop}/admin/oauth/access_token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read())
            token = res.get("access_token")
            if not token:
                print("Automatic Shopify setup: No access token in response.")
                return
    except Exception as e:
        print(f"Automatic Shopify setup: Token exchange failed: {e}")
        return
        
    # 2. Update Shopify Setting Singleton DocType
    doc = frappe.get_doc("Shopify Setting")
    doc.enable_shopify = 1
    doc.shopify_url = shop
    doc.password = token

    # Mock frappe.request to prevent "RuntimeError: object is not bound" during CLI migrate
    class MockRequest:
        def __init__(self, host):
            self.host = host

    frappe.local.request = MockRequest("erp-test.gainandshine.com")
    
    try:
        doc.save(ignore_permissions=True)
    finally:
        if hasattr(frappe.local, "request"):
            delattr(frappe.local, "request")

    frappe.db.commit()
    print("Automatic Shopify setup: Database Shopify Setting updated.")
    
    # 3. Update site_config.json
    site_config_path = frappe.get_site_path("site_config.json")
    if os.path.exists(site_config_path):
        with open(site_config_path, "r") as f:
            cfg = json.load(f)
    else:
        cfg = {}
        
    cfg["shopify_access_token"] = token
    cfg["shopify_domain"] = shop
    cfg["shopify_client_id"] = client_id
    cfg["shopify_client_secret"] = client_secret
    
    with open(site_config_path, "w") as f:
        json.dump(cfg, f, indent=1)
        
    frappe.conf.update(cfg)
    print("Automatic Shopify setup: site_config.json updated.")
    
    # 4. Register Webhooks using ShopifyClient
    try:
        # Determine host_url dynamically
        host_url = None
        for host in ["host.docker.internal", "172.17.0.1", "localhost"]:
            try:
                tunnel_req = urllib.request.Request(f"http://{host}:4040/api/tunnels", headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(tunnel_req, timeout=1) as resp:
                    t_data = json.loads(resp.read().decode())
                    tunnels = t_data.get("tunnels", [])
                    if tunnels:
                        host_url = tunnels[0]["public_url"]
                        break
            except Exception:
                continue
                
        if not host_url:
            host_url = os.environ.get("SHOPIFY_NGROK_URL") or getattr(frappe.conf, "shopify_ngrok_url", None) or "https://your-ngrok-domain.ngrok-free.app"
            
        print(f"Automatic Shopify setup: Registering webhooks pointing to {host_url}...")
        from erpops.erpops.shopify.shopify_client import ShopifyClient
        client = ShopifyClient()
        results = client.register_webhooks(host_url)
        for res in results:
            print(f"  - Webhook {res['topic']}: {res['status']} {res.get('message', '')}")
            
    except Exception as e:
        print(f"Automatic Shopify setup: Failed to register webhooks: {e}")
