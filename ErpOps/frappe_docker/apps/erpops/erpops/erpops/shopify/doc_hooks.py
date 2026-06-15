import frappe
import json
import os

def update_site_config(doc, method):
    """
    Hook triggered on Shopify Setting save.
    Syncs database settings to site_config.json so ShopifyClient can authenticate.
    """
    password = doc.get_password("password") if hasattr(doc, "get_password") else doc.password
    if not doc.enable_shopify or not password or not doc.shopify_url:
        return

    # Clean shop domain
    shop = doc.shopify_url.replace("https://", "").replace("http://", "").rstrip("/")
    if not shop.endswith(".myshopify.com"):
        shop = f"{shop}.myshopify.com"

    site_config_path = frappe.get_site_path("site_config.json")
    if os.path.exists(site_config_path):
        with open(site_config_path, "r") as f:
            cfg = json.load(f)
    else:
        cfg = {}

    # Read Client ID & Secret from environment if not present in site_config
    client_id = os.environ.get("SHOPIFY_CLIENT_ID") or cfg.get("shopify_client_id", "")
    client_secret = os.environ.get("SHOPIFY_CLIENT_SECRET") or cfg.get("shopify_client_secret", "")

    cfg["shopify_access_token"] = password
    cfg["shopify_domain"] = shop
    if client_id:
        cfg["shopify_client_id"] = client_id
    if client_secret:
        cfg["shopify_client_secret"] = client_secret

    with open(site_config_path, "w") as f:
        json.dump(cfg, f, indent=1)
    
    # Reload local conf
    frappe.conf.update(cfg)
    frappe.logger().info(f"Successfully synced Shopify Setting to site_config.json for shop: {shop}")
