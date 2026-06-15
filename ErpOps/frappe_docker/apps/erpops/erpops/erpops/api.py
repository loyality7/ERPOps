import frappe
from frappe import _
import json
from datetime import datetime, timedelta


@frappe.whitelist()
def get_feed_items():
    """Returns all open/snoozed Marketplace Alert rows sorted by severity."""
    now = frappe.utils.now_datetime()
    severity_order = {"fire": 1, "warn": 2, "info": 3}
    alerts = frappe.get_all(
        "Marketplace Alert",
        filters=[["status", "in", ["Open", "Snoozed"]]],
        fields=[
            "name", "alert_type", "severity", "title", "description",
            "item_code", "sales_order", "marketplace", "status",
            "snoozed_until", "ai_note", "creation",
        ],
        order_by="creation desc",
        limit=50,
    )
    result = []
    for a in alerts:
        if a.status == "Snoozed" and a.snoozed_until and a.snoozed_until > now:
            continue
        result.append(a)
    result.sort(key=lambda x: (severity_order.get(x.get("severity", "info"), 3), str(x.get("creation", ""))))
    return result


@frappe.whitelist()
def get_kpi_summary():
    """Returns KPI summary for the dashboard header strip."""
    today = frappe.utils.today()
    yesterday = frappe.utils.add_days(today, -1)

    orders_today = frappe.db.count("Sales Order", {"transaction_date": today, "docstatus": 1})
    orders_yesterday = frappe.db.count("Sales Order", {"transaction_date": yesterday, "docstatus": 1})

    revenue_today = frappe.db.sql("""
        SELECT IFNULL(SUM(grand_total), 0) FROM `tabSales Order`
        WHERE transaction_date = %s AND docstatus = 1
    """, today)[0][0]

    revenue_yesterday = frappe.db.sql("""
        SELECT IFNULL(SUM(grand_total), 0) FROM `tabSales Order`
        WHERE transaction_date = %s AND docstatus = 1
    """, yesterday)[0][0]

    fires = frappe.db.count("Marketplace Alert", {"severity": "fire", "status": "Open"})
    warns = frappe.db.count("Marketplace Alert", {"severity": "warn", "status": "Open"})

    wh_stock = frappe.db.sql("""
        SELECT IFNULL(SUM(actual_qty), 0) FROM `tabBin` WHERE actual_qty > 0
    """)[0][0]

    sku_count = frappe.db.sql("""
        SELECT COUNT(DISTINCT item_code) FROM `tabBin` WHERE actual_qty > 0
    """)[0][0]

    shopify_connected = False
    shopify_domain = "Not Connected"
    last_sync_str = "Never"
    
    try:
        shopify_settings = frappe.get_doc("Shopify Setting")
        shopify_connected = bool(shopify_settings.enable_shopify and shopify_settings.password)
        shopify_domain = shopify_settings.shopify_url or "Not Connected"
        if shopify_settings.last_inventory_sync:
            last_sync_str = frappe.utils.format_datetime(shopify_settings.last_inventory_sync)
    except Exception as e:
        frappe.logger().error(f"Error reading Shopify Settings for KPI: {e}")

    shopify_orders_count = frappe.db.count("Sales Order", {"custom_channel": "shopify"})

    return {
        "orders_today": int(orders_today),
        "orders_yesterday": int(orders_yesterday),
        "revenue_today": float(revenue_today),
        "revenue_yesterday": float(revenue_yesterday),
        "items_to_action": int(fires + warns),
        "fires": int(fires),
        "warns": int(warns),
        "wh_stock": int(wh_stock),
        "sku_count": int(sku_count),
        "account_health": {},
        "shopify_connected": shopify_connected,
        "shopify_domain": shopify_domain,
        "shopify_last_sync": last_sync_str,
        "shopify_orders_count": int(shopify_orders_count),
    }


@frappe.whitelist()
def get_inventory_with_velocity():
    """Returns inventory table with stock, velocity, days cover per SKU per warehouse."""
    bins = frappe.db.sql("""
        SELECT
            i.name AS item_code,
            i.item_name,
            COALESCE(b.warehouse, 'No Warehouse') AS warehouse,
            COALESCE(b.actual_qty, 0) AS actual_qty,
            COALESCE(b.reserved_qty, 0) AS reserved_qty,
            COALESCE(b.actual_qty - b.reserved_qty, 0) AS available_qty
        FROM `tabItem` i
        LEFT JOIN `tabBin` b ON i.name = b.item_code
        ORDER BY i.name
    """, as_dict=True)

    fourteen_days_ago = frappe.utils.add_days(frappe.utils.today(), -14)
    velocity_data = frappe.db.sql("""
        SELECT
            soi.item_code,
            SUM(soi.qty) / 14.0 AS daily_velocity
        FROM `tabSales Order Item` soi
        JOIN `tabSales Order` so ON so.name = soi.parent
        WHERE so.transaction_date >= %s AND so.docstatus = 1
        GROUP BY soi.item_code
    """, fourteen_days_ago, as_dict=True)

    velocity_map = {v.item_code: v.daily_velocity for v in velocity_data}

    result = []
    for b in bins:
        velocity = velocity_map.get(b.item_code, 0)
        days_cover = round(b.available_qty / velocity, 1) if velocity > 0 else 999

        reorder_policy = frappe.db.get_value(
            "Reorder Policy",
            {"item_code": b.item_code, "warehouse": b.warehouse},
            ["reorder_point", "safety_stock"],
        )

        if reorder_policy:
            rp, ss = reorder_policy
            if b.actual_qty <= (ss or 0):
                status = "Low"
            elif b.actual_qty <= (rp or 0):
                status = "Reorder"
            else:
                status = "Healthy"
        else:
            if days_cover < 5:
                status = "Low"
            elif days_cover < 14:
                status = "Reorder"
            else:
                status = "Healthy"

        channel_skus = frappe.get_all(
            "Ecommerce Item",
            filters={"erpnext_item_code": b.item_code},
            fields=["integration", "sku"],
        )
        channels = [c.integration for c in channel_skus]

        result.append({
            **b,
            "daily_velocity": round(velocity, 1),
            "days_cover": days_cover,
            "status": status,
            "channels": channels,
        })

    return result


@frappe.whitelist()
def snooze_alert(alert_id, hours=24):
    """Snooze a Marketplace Alert for N hours."""
    hours = int(hours)
    snoozed_until = frappe.utils.add_to_date(frappe.utils.now_datetime(), hours=hours)
    frappe.set_value("Marketplace Alert", alert_id, {
        "status": "Snoozed",
        "snoozed_until": snoozed_until,
    })
    frappe.db.commit()
    return {"snoozed_until": str(snoozed_until)}


@frappe.whitelist()
def approve_reorder(item_code, qty, supplier=None):
    """Create a Draft Purchase Order for a reorder."""
    qty = float(qty)

    policy = frappe.db.get_value(
        "Reorder Policy",
        {"item_code": item_code},
        ["preferred_supplier", "unit_cost_cny", "unit_cost_inr", "warehouse", "lead_time_days", "reorder_qty"],
        as_dict=True,
    )

    supplier = supplier or (policy.preferred_supplier if policy else None)
    unit_rate = float(policy.unit_cost_inr or 0) if policy else 0
    lead_time = int(policy.lead_time_days or 14) if policy else 14

    po = frappe.new_doc("Purchase Order")
    po.supplier = supplier
    po.schedule_date = frappe.utils.add_days(frappe.utils.today(), lead_time)
    po.currency = "INR"
    po.append("items", {
        "item_code": item_code,
        "qty": qty,
        "rate": unit_rate,
        "schedule_date": po.schedule_date,
        "warehouse": policy.warehouse if policy else None,
    })
    po.flags.ignore_mandatory = True
    po.insert()

    existing_alert = frappe.db.get_value(
        "Marketplace Alert",
        {"item_code": item_code, "alert_type": "Reorder", "status": ["in", ["Open", "Snoozed"]]},
    )
    if existing_alert:
        frappe.set_value("Marketplace Alert", existing_alert, {
            "status": "Resolved",
            "action_taken": f"Purchase Order {po.name} created for {qty} units",
            "resolved_at": frappe.utils.now_datetime(),
        })

    frappe.db.commit()
    return {"purchase_order": po.name, "status": "created"}


@frappe.whitelist()
def mark_dispatched(sales_order_ids, carrier, awb_number, notify_customer=True):
    """Submit a Delivery Note with tracking for one or more Sales Orders."""
    if isinstance(sales_order_ids, str):
        sales_order_ids = json.loads(sales_order_ids)

    created = []
    for so_id in sales_order_ids:
        so = frappe.get_doc("Sales Order", so_id)

        dn = frappe.new_doc("Delivery Note")
        dn.customer = so.customer
        dn.company = so.company
        dn.posting_date = frappe.utils.today()
        dn.lr_no = awb_number
        dn.lr_date = frappe.utils.today()
        dn.transporter_name = carrier

        for item in so.items:
            if item.qty > item.delivered_qty:
                dn.append("items", {
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "qty": item.qty - item.delivered_qty,
                    "rate": item.rate,
                    "against_sales_order": so_id,
                    "so_detail": item.name,
                    "warehouse": item.warehouse,
                })

        if not dn.items:
            continue

        dn.flags.ignore_mandatory = True
        dn.insert()
        dn.submit()
        created.append(dn.name)

        existing_alert = frappe.db.get_value(
            "Marketplace Alert",
            {"sales_order": so_id, "alert_type": "Late Shipment", "status": ["in", ["Open", "Snoozed"]]},
        )
        if existing_alert:
            frappe.set_value("Marketplace Alert", existing_alert, {
                "status": "Resolved",
                "action_taken": f"Delivery Note {dn.name} created, AWB: {awb_number}",
                "resolved_at": frappe.utils.now_datetime(),
            })

    frappe.db.commit()
    return {"delivery_notes": created, "awb": awb_number}


@frappe.whitelist()
def shopify_get_orders(limit=25):
    """Pull recent Shopify orders via GraphQL."""
    from erpops.erpops.shopify.shopify_client import ShopifyClient
    shopify = ShopifyClient()
    return shopify.get_orders(limit=int(limit))


@frappe.whitelist()
def shopify_fulfill_order(order_id, carrier, awb_number, notify_customer=True):
    """Fulfill a Shopify order via GraphQL fulfillmentCreate."""
    from erpops.erpops.shopify.shopify_client import ShopifyClient
    shopify = ShopifyClient()
    return shopify.fulfill_order(
        order_id=order_id,
        carrier=carrier,
        tracking_number=awb_number,
        notify_customer=bool(notify_customer),
    )


@frappe.whitelist()
def shopify_reprice(product_id, variant_id, price, compare_at_price=None):
    """Update price on a Shopify product variant."""
    from erpops.erpops.shopify.shopify_client import ShopifyClient
    shopify = ShopifyClient()
    return shopify.update_variant_price(
        product_id=product_id,
        variant_id=variant_id,
        price=str(price),
        compare_at_price=str(compare_at_price) if compare_at_price else None,
    )


@frappe.whitelist()
def shopify_update_inventory(inventory_item_id, location_id, qty):
    """Set absolute inventory quantity on Shopify."""
    from erpops.erpops.shopify.shopify_client import ShopifyClient
    shopify = ShopifyClient()
    return shopify.set_inventory(
        inventory_item_id=inventory_item_id,
        location_id=location_id,
        quantity=int(qty),
    )


@frappe.whitelist()
def ask_erpops(question):
    """Answer a natural language question about the brand's ops data from ERPNext."""
    import re
    q = (question or "").lower()

    # ── Reorder / stock ─────────────────────────────────────────
    if re.search(r"reorder|stock|inventory|low", q):
        items = get_inventory_with_velocity()
        low = [i for i in items if (i.get("days_cover") or 999) <= 14]
        if not low:
            return {"answer": "No SKUs are below the 14-day reorder threshold right now."}
        lines = []
        for i in low:
            lines.append(f"• {i['item_code']} — {i.get('actual_qty', 0)} units, {i.get('days_cover', '?')}d cover")
        return {"answer": "SKUs needing reorder:\n" + "\n".join(lines)}

    # ── Late shipment ─────────────────────────────────────────────
    if re.search(r"late|shipment|ship today|dispatch", q):
        today = frappe.utils.today()
        orders = frappe.get_all(
            "Sales Order",
            filters=[["delivery_date", "<=", today], ["status", "in", ["To Deliver and Bill", "To Deliver"]]],
            fields=["name", "delivery_date", "customer"],
            limit=10,
        )
        if not orders:
            return {"answer": "No orders at late-shipment risk today."}
        lines = [
            f"• {o['name']} — {o['customer']} (due {o['delivery_date']})".replace("None", "?")
            for o in orders
        ]
        return {"answer": f"{len(orders)} order(s) at late-shipment risk:\n" + "\n".join(lines)}

    # ── Return rate ─────────────────────────────────────────────
    if re.search(r"return|refund", q):
        week_ago = frappe.utils.add_days(frappe.utils.today(), -7)
        total = frappe.db.count("Sales Order", {"transaction_date": [">=", week_ago]}) or 1
        returned = frappe.db.count("Sales Order", {
            "transaction_date": [">=", week_ago],
            "status": "Cancelled",
        }) or 0
        rate = round(returned / total * 100, 1)
        return {"answer": f"Return/cancel rate this week: {rate}% ({returned} of {total} orders)."}

    # ── Revenue ─────────────────────────────────────────────────
    if re.search(r"revenue|sales|today", q):
        kpi = get_kpi_summary()
        today_rev = kpi.get("revenue_today", 0)
        yest_rev = kpi.get("revenue_yesterday", 0)
        pct = round((today_rev - yest_rev) / yest_rev * 100, 1) if yest_rev else 0
        direction = "↑" if pct >= 0 else "↓"
        return {
            "answer": (
                f"Today: ₹{today_rev:,.0f} ({kpi.get('orders_today', 0)} orders)\n"
                f"Yesterday: ₹{yest_rev:,.0f}\n"
                f"{direction} {abs(pct)}% vs yesterday"
            )
        }

    # ── Generic fallback ─────────────────────────────────────────
    return {
        "answer": (
            f'I couldn\'t find specific data for "{question}". '
            'Try: "Which SKUs need reorder?", "Revenue today", '
            '"Late shipment risk", "Return rate".'
        ),
    }


@frappe.whitelist(allow_guest=True)
def shopify_oauth_callback():
    """
    Shopify OAuth callback — receives ?code= redirect, exchanges for shpat_ token,
    saves to site_config.json. Redirects user directly to the new dashboard page in desk.
    """
    import urllib.request
    import urllib.parse

    import os
    code = frappe.request.args.get("code", "")
    shop = frappe.request.args.get("shop", "")

    if not code:
        return {"error": "No code in request", "args": dict(frappe.request.args)}

    client_id = getattr(frappe.conf, "shopify_client_id", "") or os.environ.get("SHOPIFY_CLIENT_ID", "")
    client_secret = getattr(frappe.conf, "shopify_client_secret", "") or os.environ.get("SHOPIFY_CLIENT_SECRET", "")

    post_data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
    }).encode()

    req = urllib.request.Request(
        "https://" + shop + "/admin/oauth/access_token",
        data=post_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    with urllib.request.urlopen(req) as r:
        result = json.loads(r.read())

    token = result.get("access_token", "")

    if token:
        site_config_path = frappe.get_site_path("site_config.json")
        with open(site_config_path) as f:
            cfg = json.load(f)
        cfg["shopify_access_token"] = token
        cfg["shopify_domain"] = shop
        with open(site_config_path, "w") as f:
            json.dump(cfg, f, indent=1)

        # Automatically register webhook subscriptions using the dynamic host URL
        try:
            x_original_host = frappe.local.request.headers.get("X-Original-Host")
            x_forwarded_host = frappe.local.request.headers.get("X-Forwarded-Host")
            host = x_original_host or x_forwarded_host or frappe.local.request.host
            host_url = f"https://{host}"
            
            # Temporary set context so ShopifyClient can authenticate immediately
            frappe.conf.shopify_access_token = token
            frappe.conf.shopify_domain = shop
            
            from erpops.erpops.shopify.shopify_client import ShopifyClient
            client = ShopifyClient()
            client.register_webhooks(host_url)
        except Exception as e:
            frappe.logger().error(f"Failed to auto-register webhooks during OAuth: {e}")

        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = (
            "/app/erpops_dashboard?shopify_connected=1&shop=" + shop
        )

    return {"token_saved": bool(token), "shop": shop}


@frappe.whitelist()
def shopify_get_products(limit=50):
    """Pull products from Shopify via GraphQL."""
    from erpops.erpops.shopify.shopify_client import ShopifyClient
    shopify = ShopifyClient()
    return shopify.get_products(limit=int(limit))


@frappe.whitelist()
def run_manual_sync():
    """Manually trigger Shopify orders and products sync."""
    from erpops.erpops.scheduler.shopify_order_sync import sync_shopify_orders, sync_shopify_products
    sync_shopify_products()
    sync_shopify_orders()
    return {"status": "success"}


@frappe.whitelist()
def get_shopify_connect_url():
    """
    Dynamically generate the Shopify OAuth authorization URL.
    Reads client_id and shop domain from env vars or site_config.
    Returns the full URL the user should visit to install/authorize the app.
    """
    import os

    client_id = os.environ.get("SHOPIFY_CLIENT_ID") or getattr(frappe.conf, "shopify_client_id", "")
    shop = os.environ.get("SHOPIFY_SHOP") or getattr(frappe.conf, "shopify_domain", "")

    if not client_id:
        return {"error": "SHOPIFY_CLIENT_ID not configured. Set it in .env or site_config.json."}
    if not shop:
        return {"error": "SHOPIFY_SHOP not configured. Set it in .env or site_config.json."}

    # Clean shop domain
    shop = shop.replace("https://", "").replace("http://", "").rstrip("/")
    if not shop.endswith(".myshopify.com"):
        shop = f"{shop}.myshopify.com"

    # Detect ngrok/public host URL for the redirect_uri
    host_url = None
    try:
        import urllib.request
        tunnel_req = urllib.request.Request("http://host.docker.internal:4040/api/tunnels", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(tunnel_req, timeout=2) as resp:
            t_data = json.loads(resp.read().decode())
            tunnels = t_data.get("tunnels", [])
            if tunnels:
                host_url = tunnels[0]["public_url"]
    except Exception:
        pass

    if not host_url:
        # Fallback: use X-Forwarded headers or env
        host_url = os.environ.get("SHOPIFY_NGROK_URL", "")
        if not host_url:
            x_host = frappe.local.request.headers.get("X-Original-Host") or frappe.local.request.headers.get("X-Forwarded-Host")
            scheme = frappe.local.request.scheme or "https"
            if x_host:
                host_url = f"{scheme}://{x_host}"
            else:
                host_url = f"{scheme}://{frappe.local.request.host}"

    redirect_uri = f"{host_url}/api/method/erpops.erpops.shopify.oauth_callback.oauth_callback"

    scopes = "read_orders,write_orders,read_products,write_products,read_inventory,write_inventory,read_fulfillments,write_fulfillments"

    auth_url = f"https://{shop}/admin/oauth/authorize?client_id={client_id}&scope={scopes}&redirect_uri={redirect_uri}"

    return {
        "url": auth_url,
        "shop": shop,
        "redirect_uri": redirect_uri,
    }

@frappe.whitelist()
def get_product_catalogue():
    """Returns detailed product catalogue for Alaiy OS inventory view."""
    try:
        items = frappe.db.sql("""
            SELECT
                i.name AS item_code,
                i.item_name,
                COALESCE(i.image, p_item.image) AS image,
                COALESCE(i.brand, p_item.brand) AS brand,
                i.has_variants,
                i.variant_of,
                i.item_group,
                SUM(COALESCE(b.actual_qty, 0)) AS actual_qty,
                SUM(COALESCE(b.actual_qty - b.reserved_qty, 0)) AS available_qty
            FROM `tabItem` i
            LEFT JOIN `tabItem` p_item ON i.variant_of = p_item.name
            LEFT JOIN `tabBin` b ON i.name = b.item_code
            WHERE (i.item_group = 'Shopify Items' 
               OR i.name IN (SELECT erpnext_item_code FROM `tabEcommerce Item` WHERE integration = 'Shopify'))
               AND (i.variant_of IS NULL OR i.variant_of = '')
            GROUP BY i.name
            ORDER BY i.creation DESC
        """, as_dict=True)
        
        # Get all Shopify integrations mapping safely
        mapping_map = {}
        try:
            mappings = frappe.get_all(
                "Ecommerce Item",
                fields=["erpnext_item_code", "integration_item_code", "integration"]
            )
            for m in mappings:
                if m.integration == "Shopify":
                    mapping_map[m.erpnext_item_code] = m.integration_item_code
        except Exception as e:
            frappe.logger().error(f"Error loading Ecommerce Item mappings: {e}")
            
        # Calculate variants count
        templates = [i.item_code for i in items if i.has_variants]
        variant_counts = {}
        if templates:
            counts = frappe.db.sql("""
                SELECT variant_of, COUNT(*) as count 
                FROM `tabItem` 
                WHERE variant_of IN %s 
                GROUP BY variant_of
            """, (templates,), as_dict=True)
            variant_counts = {c.variant_of: c.count for c in counts}
            
        result = []
        for i in items:
            var_count = 1
            if i.has_variants:
                var_count = variant_counts.get(i.item_code, 0)
                
            shopify_id = mapping_map.get(i.item_code)
            
            # Robust fallback for imported or numeric Shopify codes
            is_shopify_group = i.item_group == "Shopify Items"
            is_shopify_numeric = i.item_code.isdigit() and len(i.item_code) > 10
            
            if not shopify_id and (is_shopify_group or is_shopify_numeric):
                shopify_id = i.item_code
                
            is_synced = "Synced" if (shopify_id or is_shopify_group or is_shopify_numeric) else "Not synced"
            
            result.append({
                "item_code": i.item_code,
                "item_name": i.item_name,
                "image": i.image or "/assets/erpops/images/logo.png",
                "brand": i.brand or "Generic",
                "variants": f"{var_count} variant" if var_count == 1 else f"{var_count} variants",
                "has_variants": int(i.has_variants or 0),
                "available": int(i.available_qty),
                "on_hand": int(i.actual_qty),
                "shopify_status": is_synced,
                "shopify_id": shopify_id
            })
        return result
    except Exception as e:
        frappe.log_error(f"Error loading product catalogue: {e}", "ErpOps")
        return []

@frappe.whitelist()
def get_item_variants(item_code):
    """Returns list of variants for a template item, including their inventory quantities."""
    try:
        variants = frappe.db.sql("""
            SELECT
                i.name AS item_code,
                i.item_name,
                COALESCE(i.image, p_item.image) AS image,
                COALESCE(i.brand, p_item.brand) AS brand,
                SUM(COALESCE(b.actual_qty, 0)) AS actual_qty,
                SUM(COALESCE(b.actual_qty - b.reserved_qty, 0)) AS available_qty
            FROM `tabItem` i
            LEFT JOIN `tabItem` p_item ON i.variant_of = p_item.name
            LEFT JOIN `tabBin` b ON i.name = b.item_code
            WHERE i.variant_of = %s
            GROUP BY i.name
            ORDER BY i.name ASC
        """, (item_code,), as_dict=True)
        
        # Get Shopify integration mapping safely
        mapping_map = {}
        try:
            mappings = frappe.get_all(
                "Ecommerce Item",
                filters={"erpnext_item_code": ["in", [v.item_code for v in variants]]},
                fields=["erpnext_item_code", "integration_item_code", "integration"]
            )
            for m in mappings:
                if m.integration == "Shopify":
                    mapping_map[m.erpnext_item_code] = m.integration_item_code
        except Exception:
            pass
            
        result = []
        for v in variants:
            shopify_id = mapping_map.get(v.item_code)
            is_shopify_group = v.item_code.startswith("SPY-") or v.item_group == "Shopify Items"
            is_shopify_numeric = v.item_code.isdigit() and len(v.item_code) > 10
            
            if not shopify_id and (is_shopify_group or is_shopify_numeric):
                shopify_id = v.item_code
                
            is_synced = "Synced" if (shopify_id or is_shopify_group or is_shopify_numeric) else "Not synced"
            
            result.append({
                "item_code": v.item_code,
                "item_name": v.item_name,
                "image": v.image or "/assets/erpops/images/logo.png",
                "brand": v.brand or "Generic",
                "available": int(v.available_qty),
                "on_hand": int(v.actual_qty),
                "shopify_status": is_synced,
                "shopify_id": shopify_id
            })
        return result
    except Exception as e:
        frappe.log_error(f"Error loading item variants: {e}", "ErpOps")
        return []
        

@frappe.whitelist()
def toggle_shopify_status(enable):
    """Enables or disables the Shopify integration."""
    try:
        enable = int(enable)
        doc = frappe.get_doc("Shopify Setting")
        doc.enable_shopify = enable
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return {"success": True, "enable_shopify": doc.enable_shopify}
    except Exception as e:
        frappe.log_error("Failed to toggle Shopify status", "ErpOps")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_shopify_status():
    """Returns the current status of the Shopify integration."""
    try:
        doc = frappe.get_doc("Shopify Setting")
        last_sync = frappe.db.get_single_value("Shopify Setting", "last_inventory_sync")
        if last_sync:
            last_sync = frappe.utils.format_datetime(last_sync)
        else:
            last_sync = "Never synced"
            
        return {
            "success": True,
            "enable_shopify": doc.enable_shopify or 0,
            "shopify_url": doc.shopify_url or "Not configured",
            "last_sync": last_sync
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_sales_orders():
    """Returns list of Sales Orders for Alaiy OS orders view."""
    try:
        orders = frappe.db.sql("""
            SELECT
                so.name AS id,
                so.customer_name AS customer,
                so.transaction_date AS date,
                so.grand_total AS total,
                COALESCE(so.custom_payment_status, 'Unpaid') AS payment,
                so.status AS fulfillment,
                COALESCE(so.custom_channel, 'ERPNext') AS channel
            FROM `tabSales Order` so
            ORDER BY so.creation DESC
            LIMIT 100
        """, as_dict=True)
        
        # Format values nicely
        for o in orders:
            o.total = f"₹{o.total:,.2f}"
            o.date = str(o.date)
            # Standardize status labels
            if o.fulfillment == "Draft":
                o.fulfillment = "Processing"
            elif o.fulfillment == "Completed":
                o.fulfillment = "Fulfilled"
            elif o.fulfillment == "Cancelled":
                o.fulfillment = "Returned"
                
        return orders
    except Exception as e:
        frappe.log_error(f"Error fetching sales orders: {e}", "ErpOps API")
        return []
