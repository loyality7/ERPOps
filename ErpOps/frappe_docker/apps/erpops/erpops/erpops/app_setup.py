import frappe

def after_migrate():
    create_custom_fields()
    ensure_module_def()
    setup_workspace()
    hide_standard_workspaces()
    setup_shopify_integration()
    setup_branding()

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
        "Utilities", "ERPNext Settings", "ERPNext Integrations"
    ]
    for name in workspaces_to_hide:
        if frappe.db.exists("Workspace", name):
            frappe.db.set_value("Workspace", name, "is_hidden", 1)
            
    # Make sure custom workspaces are visible, public, and flat
    for name in ["ErpOps", "Inventory", "Orders", "Returns", "Analytics", "Channels"]:
        if frappe.db.exists("Workspace", name):
            frappe.db.set_value("Workspace", name, "is_hidden", 0)
            frappe.db.set_value("Workspace", name, "public", 1)
            frappe.db.set_value("Workspace", name, "parent_page", "")
        
    frappe.db.commit()
    
    # Programmatically construct sidebar workspaces
    setup_sidebar_workspaces()

def setup_sidebar_workspaces():
    """Setup custom Inventory and Orders workspaces in the sidebar."""
    import json
    
    # 1. Setup Inventory Workspace
    if frappe.db.exists("Workspace", "Inventory"):
        inv_ws = frappe.get_doc("Workspace", "Inventory")
    else:
        inv_ws = frappe.new_doc("Workspace")
        inv_ws.name = "Inventory"
        inv_ws.label = "Inventory"
        inv_ws.title = "Inventory"
        inv_ws.icon = "stock"
        inv_ws.public = 1
        inv_ws.module = "ErpOps"
        
    inv_ws.public = 1
    inv_ws.module = "ErpOps"
    inv_ws.parent_page = ""
    inv_ws.is_hidden = 0
    inv_ws.sequence_id = 2
    inv_ws.links = []
    inv_ws.append("links", {
        "type": "Card Break",
        "label": "Inventory View"
    })
    inv_ws.append("links", {
        "link_type": "DocType",
        "link_to": "Item",
        "label": "Product Catalogue",
        "type": "Link",
        "icon": "item"
    })
    inv_ws.append("links", {
        "link_type": "DocType",
        "link_to": "Warehouse",
        "label": "Warehouses",
        "type": "Link",
        "icon": "warehouse"
    })
    
    inv_ws.shortcuts = []
    inv_ws.append("shortcuts", {
        "type": "DocType",
        "link_to": "Item",
        "label": "Product Catalogue",
        "icon": "item",
        "color": "Blue"
    })
    
    inv_ws.content = json.dumps([
        {"id": "inv_h1", "type": "header", "data": {"text": "<span class=\"h3\"><b>Inventory</b></span>", "col": 12}},
        {"id": "inv_sub", "type": "header", "data": {"text": "<span class=\"text-muted\">Full product catalogue — every SKU across all suppliers and channels.</span>", "col": 12}},
        {"id": "inv_sc1", "type": "shortcut", "data": {"shortcut_name": "Product Catalogue", "label": "Product Catalogue", "icon": "item", "color": "Blue", "col": 4}},
        {"id": "inv_sp1", "type": "spacer", "data": {"col": 12}}
    ])
    inv_ws.save(ignore_permissions=True)
    
    # 2. Setup Orders Workspace
    if frappe.db.exists("Workspace", "Orders"):
        ord_ws = frappe.get_doc("Workspace", "Orders")
    else:
        ord_ws = frappe.new_doc("Workspace")
        ord_ws.name = "Orders"
        ord_ws.label = "Orders"
        ord_ws.title = "Orders"
        ord_ws.icon = "sell"
        ord_ws.public = 1
        ord_ws.module = "ErpOps"
        
    ord_ws.public = 1
    ord_ws.module = "ErpOps"
    ord_ws.parent_page = ""
    ord_ws.is_hidden = 0
    ord_ws.sequence_id = 3
    ord_ws.links = []
    ord_ws.append("links", {
        "type": "Card Break",
        "label": "Order View"
    })
    ord_ws.append("links", {
        "link_type": "DocType",
        "link_to": "Sales Order",
        "label": "Sales Orders",
        "type": "Link",
        "icon": "sales"
    })
    ord_ws.append("links", {
        "link_type": "DocType",
        "link_to": "Sales Invoice",
        "label": "Sales Invoices",
        "type": "Link",
        "icon": "invoice"
    })
    
    ord_ws.shortcuts = []
    ord_ws.append("shortcuts", {
        "type": "DocType",
        "link_to": "Sales Order",
        "label": "Sales Orders",
        "icon": "sales",
        "color": "Green"
    })
    
    ord_ws.content = json.dumps([
        {"id": "ord_h1", "type": "header", "data": {"text": "<span class=\"h3\"><b>Orders</b></span>", "col": 12}},
        {"id": "ord_sub", "type": "header", "data": {"text": "<span class=\"text-muted\">Manage and view customer sales orders and invoices.</span>", "col": 12}},
        {"id": "ord_sc1", "type": "shortcut", "data": {"shortcut_name": "Sales Orders", "label": "Sales Orders", "icon": "sales", "color": "Green", "col": 4}},
        {"id": "ord_sp1", "type": "spacer", "data": {"col": 12}}
    ])
    ord_ws.save(ignore_permissions=True)
    
    # 2b. Setup Returns Workspace (Flat in sidebar)
    if frappe.db.exists("Workspace", "Returns"):
        ret_ws = frappe.get_doc("Workspace", "Returns")
    else:
        ret_ws = frappe.new_doc("Workspace")
        ret_ws.name = "Returns"
        ret_ws.label = "Returns"
        ret_ws.title = "Returns"
        ret_ws.icon = "reply"
        ret_ws.public = 1
        ret_ws.module = "ErpOps"
        
    ret_ws.public = 1
    ret_ws.module = "ErpOps"
    ret_ws.parent_page = ""
    ret_ws.is_hidden = 0
    ret_ws.sequence_id = 3
    ret_ws.links = []
    ret_ws.shortcuts = []
    ret_ws.content = json.dumps([
        {"id": "ret_h1", "type": "header", "data": {"text": "<span class=\"h3\"><b>Returns</b></span>", "col": 12}},
        {"id": "ret_sub", "type": "header", "data": {"text": "<span class=\"text-muted\">Manage and view order returns and refunds.</span>", "col": 12}}
    ])
    ret_ws.save(ignore_permissions=True)

    # 2c. Setup Analytics Workspace (Flat in sidebar)
    if frappe.db.exists("Workspace", "Analytics"):
        ana_ws = frappe.get_doc("Workspace", "Analytics")
    else:
        ana_ws = frappe.new_doc("Workspace")
        ana_ws.name = "Analytics"
        ana_ws.label = "Analytics"
        ana_ws.title = "Analytics"
        ana_ws.icon = "project"
        ana_ws.public = 1
        ana_ws.module = "ErpOps"
        
    ana_ws.public = 1
    ana_ws.module = "ErpOps"
    ana_ws.parent_page = ""
    ana_ws.is_hidden = 0
    ana_ws.sequence_id = 5
    ana_ws.links = []
    ana_ws.shortcuts = []
    ana_ws.content = json.dumps([
        {"id": "ana_h1", "type": "header", "data": {"text": "<span class=\"h3\"><b>Analytics</b></span>", "col": 12}},
        {"id": "ana_sub", "type": "header", "data": {"text": "<span class=\"text-muted\">Real-time sales velocity and channel performance insights.</span>", "col": 12}}
    ])
    ana_ws.save(ignore_permissions=True)
    
    # 3. Setup Channels Workspace
    if frappe.db.exists("Workspace", "Channels"):
        chan_ws = frappe.get_doc("Workspace", "Channels")
    else:
        chan_ws = frappe.new_doc("Workspace")
        chan_ws.name = "Channels"
        chan_ws.label = "Channels"
        chan_ws.title = "Channels"
        
    chan_ws.public = 1
    chan_ws.module = "ErpOps"
    chan_ws.parent_page = ""
    chan_ws.icon = "link"
    chan_ws.is_hidden = 0
    chan_ws.sequence_id = 4
    chan_ws.links = []
    chan_ws.append("links", {
        "type": "Card Break",
        "label": "Channels View"
    })
    chan_ws.append("links", {
        "link_type": "DocType",
        "link_to": "Shopify Setting",
        "label": "Shopify Settings",
        "type": "Link",
        "icon": "setting"
    })
    
    chan_ws.shortcuts = []
    chan_ws.content = json.dumps([
        {"id": "chan_h1", "type": "header", "data": {"text": "<span class=\"h3\"><b>Channels</b></span>", "col": 12}},
        {"id": "chan_sub", "type": "header", "data": {"text": "<span class=\"text-muted\">Manage integrations and external sales channels.</span>", "col": 12}}
    ])
    chan_ws.save(ignore_permissions=True)
    
    # 4. Setup Shopify Workspace (Hidden from sidebar)
    if frappe.db.exists("Workspace", "Shopify"):
        shop_ws = frappe.get_doc("Workspace", "Shopify")
    else:
        shop_ws = frappe.new_doc("Workspace")
        shop_ws.name = "Shopify"
        shop_ws.label = "Shopify"
        shop_ws.title = "Shopify"
        shop_ws.icon = "sell"
        shop_ws.public = 1
        shop_ws.module = "ErpOps"
        
    shop_ws.icon = "sell"
    shop_ws.parent_page = ""
    shop_ws.is_hidden = 1
    shop_ws.sequence_id = 1
    shop_ws.links = []
    shop_ws.shortcuts = []
    shop_ws.content = json.dumps([
        {"id": "shop_h1", "type": "header", "data": {"text": "<span class=\"h3\"><b>Shopify</b></span>", "col": 12}},
        {"id": "shop_sub", "type": "header", "data": {"text": "<span class=\"text-muted\">Manage Shopify sync settings and connection status.</span>", "col": 12}}
    ])
    shop_ws.save(ignore_permissions=True)
    
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
    doc.shared_secret = client_secret

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

def setup_branding():
    """Configure Alaiy OS branding globally."""
    print("Setting up Alaiy OS branding...")
    
    # 1. Update System Settings
    try:
        system_settings = frappe.get_doc("System Settings")
        system_settings.app_name = "Alaiy OS"
        system_settings.save(ignore_permissions=True)
        print("  - System Settings app_name set to Alaiy OS")
    except Exception as e:
        print(f"  - Failed to update System Settings: {e}")
        
    # 2. Update Navbar Settings
    try:
        navbar_settings = frappe.get_doc("Navbar Settings")
        navbar_settings.app_logo = "/assets/erpops/images/logo.png"
        navbar_settings.save(ignore_permissions=True)
        print("  - Navbar Settings logo updated.")
    except Exception as e:
        print(f"  - Failed to update Navbar Settings: {e}")
        
    # 3. Update Website Settings
    try:
        website_settings = frappe.get_doc("Website Settings")
        website_settings.app_logo = "/assets/erpops/images/logo.png"
        website_settings.brand_html = '<span class="h4"><b>Alaiy OS</b></span>'
        website_settings.save(ignore_permissions=True)
        print("  - Website Settings brand and logo updated.")
    except Exception as e:
        print(f"  - Failed to update Website Settings: {e}")
        
    # 4. Create custom translations to replace ERPNext with Alaiy OS globally
    try:
        translations = [
            ("ERPNext", "Alaiy OS"),
            ("erpnext", "alaiy os"),
            ("Welcome to ERPNext", "Welcome to Alaiy OS"),
            ("ERPNext Settings", "Alaiy OS Settings"),
            ("ERPNext Integrations", "Alaiy OS Integrations"),
            ("Let's begin your journey with ERPNext", "Let's begin your journey with Alaiy OS")
        ]
        for source, target in translations:
            if not frappe.db.exists("Translation", {"source_text": source, "language": "en"}):
                t = frappe.new_doc("Translation")
                t.language = "en"
                t.source_text = source
                t.translated_text = target
                t.save(ignore_permissions=True)
                print(f"  - Translation created: '{source}' -> '{target}'")
    except Exception as e:
        print(f"  - Failed to update Translation table: {e}")
        
    frappe.db.commit()
