import frappe


def sync_shopify_orders():
    """Every 5 min: poll Shopify for new orders and create Sales Orders in ERPNext."""
    try:
        # Also sync products to ensure mappings and catalog are fresh
        sync_shopify_products()

        from erpops.erpops.shopify.shopify_client import ShopifyClient
        shopify = ShopifyClient()

        last_sync = (
            frappe.db.get_single_value("Shopify Setting", "last_inventory_sync")
            or frappe.utils.add_days(frappe.utils.now_datetime(), -1)
        )

        orders = shopify.get_orders(since=last_sync)

        created = 0
        for order in orders:
            shopify_id = order.get("id", "")
            if not frappe.db.exists("Sales Order", {"custom_shopify_order_id": shopify_id}):
                _create_sales_order_from_shopify(order)
                created += 1

        frappe.db.set_single_value(
            "Shopify Setting", "last_inventory_sync", frappe.utils.now_datetime()
        )
        frappe.db.commit()

        if created:
            frappe.logger().info(f"Shopify sync: created {created} Sales Orders")

    except Exception as e:
        frappe.log_error(f"Shopify order sync failed: {e}", "Shopify Order Sync")


def sync_shopify_products():
    """Poll Shopify for products and create/map them in ERPNext."""
    try:
        from erpops.erpops.shopify.shopify_client import ShopifyClient
        shopify = ShopifyClient()

        # Fetch up to 100 products from Shopify
        products = shopify.get_products(limit=100)

        for p in products:
            title = p.get("title", "")
            vendor = p.get("vendor", "")

            for v in p.get("variants", {}).get("nodes", []):
                variant_id = v.get("id", "")
                sku = v.get("sku")
                
                # If SKU is empty, generate a fallback SKU based on Variant ID
                clean_variant_id = variant_id.split("/")[-1] if "/" in variant_id else variant_id
                if not sku:
                    sku = f"SPY-{clean_variant_id}"

                variant_title = v.get("title", "")
                item_name = title
                if variant_title and variant_title != "Default Title":
                    item_name = f"{title} - {variant_title}"

                # 1. Ensure Item exists in ERPNext
                if not frappe.db.exists("Item", sku):
                    item = frappe.new_doc("Item")
                    item.item_code = sku
                    item.item_name = item_name
                    item.item_group = "Shopify Items"
                    item.brand = vendor or "Generic"
                    item.is_stock_item = 1
                    item.stock_uom = "Nos"
                    item.flags.ignore_mandatory = True
                    item.insert(ignore_permissions=True)

                # 2. Ensure Ecommerce Item mapping exists
                if clean_variant_id and not frappe.db.exists("Ecommerce Item", {"erpnext_item_code": sku, "integration": "Shopify"}):
                    eco = frappe.new_doc("Ecommerce Item")
                    eco.erpnext_item_code = sku
                    eco.integration_item_code = clean_variant_id
                    eco.integration = "Shopify"
                    eco.insert(ignore_permissions=True)

        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Shopify product sync failed: {e}", "Shopify Product Sync")


def _create_sales_order_from_shopify(order):
    """Create an ERPNext Sales Order from a Shopify GraphQL order dict."""
    customer_name = order.get("customer", {}).get("displayName", "Shopify Customer")

    customer = frappe.db.get_value("Customer", {"customer_name": customer_name})
    if not customer:
        c = frappe.new_doc("Customer")
        c.customer_name = customer_name
        c.customer_group = "Shopify"
        c.territory = "All Territories"
        c.flags.ignore_mandatory = True
        c.insert(ignore_permissions=True)
        customer = c.name

    so = frappe.new_doc("Sales Order")
    so.customer = customer
    so.transaction_date = frappe.utils.today()
    so.delivery_date = frappe.utils.add_days(frappe.utils.today(), 3)
    so.custom_shopify_order_id = order.get("id", "")
    so.custom_channel = "shopify"

    for line in order.get("lineItems", {}).get("nodes", []):
        item_code = line.get("sku") or line.get("title", "UNKNOWN")

        if not frappe.db.exists("Item", item_code):
            item = frappe.new_doc("Item")
            item.item_code = item_code
            item.item_name = line.get("title", item_code)
            item.item_group = "Shopify Items"
            item.is_stock_item = 1
            item.stock_uom = "Nos"
            item.flags.ignore_mandatory = True
            item.insert(ignore_permissions=True)

        # Build Ecommerce Item mapping on the fly during order import
        variant_id = line.get("variant", {}).get("id") if line.get("variant") else ""
        product_id = line.get("product", {}).get("id") if line.get("product") else ""
        raw_shopify_id = variant_id or product_id or ""
        clean_shopify_id = raw_shopify_id.split("/")[-1] if "/" in raw_shopify_id else raw_shopify_id

        if clean_shopify_id and not frappe.db.exists("Ecommerce Item", {"erpnext_item_code": item_code, "integration": "Shopify"}):
            try:
                eco = frappe.new_doc("Ecommerce Item")
                eco.erpnext_item_code = item_code
                eco.integration_item_code = clean_shopify_id
                eco.integration = "Shopify"
                eco.insert(ignore_permissions=True)
            except Exception as ex:
                frappe.log_error(f"Failed to auto-create Ecommerce Item mapping during order sync: {ex}", "Shopify Sync")

        so.append("items", {
            "item_code": item_code,
            "qty": float(line.get("quantity", 1)),
            "rate": float(
                line.get("originalUnitPriceSet", {}).get("shopMoney", {}).get("amount", 0)
            ),
            "delivery_date": so.delivery_date,
        })

    if so.items:
        so.flags.ignore_mandatory = True
        so.insert(ignore_permissions=True)
        so.submit()
