import frappe


def get_customer_group():
    group = None
    try:
        if frappe.get_meta("Shopify Setting").has_field("customer_group"):
            group = frappe.db.get_single_value("Shopify Setting", "customer_group")
    except Exception:
        pass
    if group and frappe.db.exists("Customer Group", {"name": group, "is_group": 0}):
        return group
    group = None
    try:
        if frappe.get_meta("Selling Settings").has_field("customer_group"):
            group = frappe.db.get_single_value("Selling Settings", "customer_group")
    except Exception:
        pass
    if group and frappe.db.exists("Customer Group", {"name": group, "is_group": 0}):
        return group
    try:
        fallback = frappe.db.get_value("Customer Group", {"is_group": 0}, "name")
        if fallback:
            return fallback
    except Exception:
        pass
    try:
        return frappe.db.get_value("Customer Group", {}, "name")
    except Exception:
        return None


def get_item_group():
    group = None
    try:
        if frappe.get_meta("Shopify Setting").has_field("item_group"):
            group = frappe.db.get_single_value("Shopify Setting", "item_group")
    except Exception:
        pass
    if group and frappe.db.exists("Item Group", {"name": group, "is_group": 0}):
        return group
    group = None
    try:
        if frappe.get_meta("Stock Settings").has_field("default_item_group"):
            group = frappe.db.get_single_value("Stock Settings", "default_item_group")
    except Exception:
        pass
    if group and frappe.db.exists("Item Group", {"name": group, "is_group": 0}):
        return group
    try:
        fallback = frappe.db.get_value("Item Group", {"is_group": 0}, "name")
        if fallback:
            return fallback
    except Exception:
        pass
    try:
        return frappe.db.get_value("Item Group", {}, "name")
    except Exception:
        return None


def sync_shopify_orders():
    try:
        sync_shopify_products()
        from erpops.erpops.shopify.shopify_client import ShopifyClient
        shopify = ShopifyClient()

        sync_old = 0
        from_date = None
        to_date = None
        try:
            meta = frappe.get_meta("Shopify Setting")
            if meta.has_field("custom_sync_old_orders"):
                sync_old = frappe.db.get_single_value("Shopify Setting", "custom_sync_old_orders") or 0
            if meta.has_field("custom_from_date"):
                from_date = frappe.db.get_single_value("Shopify Setting", "custom_from_date")
            if meta.has_field("custom_to_date"):
                to_date = frappe.db.get_single_value("Shopify Setting", "custom_to_date")
        except Exception:
            pass

        if sync_old and from_date:
            orders = shopify.get_orders(since=from_date, to_date=to_date)
            try:
                frappe.db.set_single_value("Shopify Setting", "custom_sync_old_orders", 0)
                frappe.db.commit()
            except Exception:
                pass
        else:
            last_sync = None
            try:
                last_sync = frappe.db.get_single_value("Shopify Setting", "last_inventory_sync")
            except Exception:
                pass
            if not last_sync:
                last_sync = frappe.utils.add_days(frappe.utils.now_datetime(), -30)
            orders = shopify.get_orders(since=last_sync)

        created = 0
        for order in orders:
            shopify_id = order.get("id", "")
            if not frappe.db.exists("Sales Order", {"custom_shopify_order_id": shopify_id}):
                try:
                    _create_sales_order_from_shopify(order)
                    created += 1
                    frappe.db.commit()
                except Exception as ord_err:
                    frappe.log_error(title="Shopify Order Sync", message=f"Failed to sync Shopify Order {order.get('name')}: {ord_err}")

        try:
            frappe.db.set_single_value("Shopify Setting", "last_inventory_sync", frappe.utils.now_datetime())
            frappe.db.commit()
        except Exception:
            pass

        if created:
            frappe.logger().info(f"Shopify sync: created {created} Sales Orders")

    except Exception as e:
        frappe.log_error(title="Shopify Order Sync", message=f"Shopify order sync failed: {e}")


def sync_shopify_products():
    try:
        from erpops.erpops.shopify.shopify_client import ShopifyClient
        shopify = ShopifyClient()
        products = shopify.get_products(limit=100)

        for p in products:
            title = p.get("title", "")
            vendor = p.get("vendor", "")

            for v in p.get("variants", {}).get("nodes", []):
                try:
                    variant_id = v.get("id", "")
                    sku = v.get("sku")
                    clean_variant_id = variant_id.split("/")[-1] if "/" in variant_id else variant_id
                    if not sku:
                        sku = f"SPY-{clean_variant_id}"

                    variant_title = v.get("title", "")
                    item_name = title
                    if variant_title and variant_title != "Default Title":
                        item_name = f"{title} - {variant_title}"

                    if not frappe.db.exists("Item", sku):
                        item = frappe.new_doc("Item")
                        item.item_code = sku
                        item.item_name = item_name
                        item.item_group = get_item_group()
                        brand_name = vendor or None
                        if brand_name and not frappe.db.exists("Brand", brand_name):
                            try:
                                b = frappe.new_doc("Brand")
                                b.brand_name = brand_name
                                b.insert(ignore_permissions=True)
                                frappe.db.commit()
                            except Exception:
                                brand_name = None
                        item.brand = brand_name
                        item.is_stock_item = 1
                        item.stock_uom = "Nos"
                        item.flags.ignore_mandatory = True
                        item.insert(ignore_permissions=True)

                    if clean_variant_id:
                        existing_by_variant = frappe.db.get_value(
                            "Ecommerce Item",
                            {"integration_item_code": clean_variant_id, "integration": "Shopify"},
                            ["name", "erpnext_item_code"],
                            as_dict=True
                        )
                        existing_by_sku = frappe.db.get_value(
                            "Ecommerce Item",
                            {"erpnext_item_code": sku, "integration": "Shopify"},
                            ["name", "integration_item_code"],
                            as_dict=True
                        )

                        if existing_by_variant:
                            if existing_by_variant.erpnext_item_code != sku:
                                try:
                                    frappe.db.set_value("Ecommerce Item", existing_by_variant.name, "erpnext_item_code", sku)
                                    frappe.db.commit()
                                except Exception as upd_err:
                                    frappe.logger().warn(f"Failed to update Ecommerce Item mapping: {upd_err}")
                        elif existing_by_sku:
                            if existing_by_sku.integration_item_code != clean_variant_id:
                                try:
                                    frappe.db.set_value("Ecommerce Item", existing_by_sku.name, "integration_item_code", clean_variant_id)
                                    frappe.db.commit()
                                except Exception as upd_err:
                                    frappe.logger().warn(f"Failed to update Ecommerce Item mapping by SKU: {upd_err}")
                        else:
                            try:
                                eco = frappe.new_doc("Ecommerce Item")
                                eco.erpnext_item_code = sku
                                eco.integration_item_code = clean_variant_id
                                eco.integration = "Shopify"
                                eco.insert(ignore_permissions=True, ignore_if_duplicate=True)
                            except Exception as eco_err:
                                frappe.logger().warn(f"Failed to create Ecommerce Item mapping: {eco_err}")
                except Exception as var_err:
                    frappe.log_error(title="Shopify Product Sync", message=f"Failed to sync variant {v.get('id')}: {var_err}")

        frappe.db.commit()
    except Exception as e:
        frappe.log_error(title="Shopify Product Sync", message=f"Shopify product sync failed: {e}")


def _create_sales_order_from_shopify(order):
    customer_name = order.get("customer", {}).get("displayName", "Shopify Customer")
    customer = frappe.db.get_value("Customer", {"customer_name": customer_name})
    if not customer:
        c = frappe.new_doc("Customer")
        c.customer_name = customer_name
        c.customer_group = get_customer_group()
        c.territory = "All Territories"
        c.flags.ignore_mandatory = True
        c.insert(ignore_permissions=True)
        customer = c.name

    so = frappe.new_doc("Sales Order")
    company = frappe.db.get_single_value("Global Defaults", "default_company")
    if not company:
        companies = frappe.get_all("Company", limit=1)
        company = companies[0].name if companies else "Gain and Shine"
    so.company = company

    currency = order.get("totalPriceSet", {}).get("shopMoney", {}).get("currencyCode")
    if not currency:
        currency = frappe.db.get_value("Company", company, "default_currency") or "INR"
    so.currency = currency

    price_list = frappe.db.get_value("Price List", {"selling": 1, "enabled": 1}, "name")
    if not price_list:
        price_list = frappe.db.get_value("Price List", {"selling": 1}, "name") or "Standard Selling"
    so.selling_price_list = price_list
    so.price_list_currency = currency
    so.customer = customer
    so.transaction_date = frappe.utils.today()
    so.delivery_date = frappe.utils.add_days(frappe.utils.today(), 3)
    so.custom_shopify_order_id = order.get("id", "")
    so.custom_channel = "shopify"

    for line in order.get("lineItems", {}).get("nodes", []):
        variant_id = line.get("variant", {}).get("id") if line.get("variant") else ""
        product_id = line.get("product", {}).get("id") if line.get("product") else ""
        raw_shopify_id = variant_id or product_id or ""
        clean_shopify_id = raw_shopify_id.split("/")[-1] if "/" in raw_shopify_id else raw_shopify_id

        item_code = None
        if clean_shopify_id:
            item_code = frappe.db.get_value("Ecommerce Item", {"integration_item_code": clean_shopify_id, "integration": "Shopify"}, "erpnext_item_code")
        if not item_code:
            item_code = line.get("sku")
        if not item_code and clean_shopify_id:
            item_code = f"SPY-{clean_shopify_id}"
        if not item_code:
            item_code = line.get("title", "UNKNOWN")

        if not frappe.db.exists("Item", item_code):
            item = frappe.new_doc("Item")
            item.item_code = item_code
            item.item_name = line.get("title", item_code)
            item.item_group = get_item_group()
            item.is_stock_item = 1
            item.stock_uom = "Nos"
            item.flags.ignore_mandatory = True
            item.insert(ignore_permissions=True)

        if clean_shopify_id:
            existing_by_variant = frappe.db.get_value(
                "Ecommerce Item",
                {"integration_item_code": clean_shopify_id, "integration": "Shopify"},
                ["name", "erpnext_item_code"],
                as_dict=True
            )
            existing_by_sku = frappe.db.get_value(
                "Ecommerce Item",
                {"erpnext_item_code": item_code, "integration": "Shopify"},
                ["name", "integration_item_code"],
                as_dict=True
            )

            if existing_by_variant:
                if existing_by_variant.erpnext_item_code != item_code:
                    try:
                        frappe.db.set_value("Ecommerce Item", existing_by_variant.name, "erpnext_item_code", item_code)
                        frappe.db.commit()
                    except Exception as upd_err:
                        frappe.log_error(title="Shopify Sync", message=f"Failed to update Ecommerce Item mapping: {upd_err}")
            elif existing_by_sku:
                if existing_by_sku.integration_item_code != clean_shopify_id:
                    try:
                        frappe.db.set_value("Ecommerce Item", existing_by_sku.name, "integration_item_code", clean_shopify_id)
                        frappe.db.commit()
                    except Exception as upd_err:
                        frappe.log_error(title="Shopify Sync", message=f"Failed to update Ecommerce Item mapping by SKU: {upd_err}")
            else:
                try:
                    eco = frappe.new_doc("Ecommerce Item")
                    eco.erpnext_item_code = item_code
                    eco.integration_item_code = clean_shopify_id
                    eco.integration = "Shopify"
                    eco.insert(ignore_permissions=True, ignore_if_duplicate=True)
                except Exception as ex:
                    frappe.log_error(title="Shopify Sync", message=f"Failed to auto-create Ecommerce Item mapping during order sync: {ex}")

        so.append("items", {
            "item_code": item_code,
            "qty": float(line.get("quantity", 1)),
            "rate": float(line.get("originalUnitPriceSet", {}).get("shopMoney", {}).get("amount", 0)),
            "delivery_date": so.delivery_date,
        })

    if so.items:
        so.flags.ignore_mandatory = True
        so.insert(ignore_permissions=True)
        so.submit()
