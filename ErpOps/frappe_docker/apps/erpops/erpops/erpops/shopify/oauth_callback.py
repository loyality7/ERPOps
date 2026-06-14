"""
Shopify OAuth callback handler for ErpOps ERPNext.
Receives the ?code= redirect, exchanges for access token, saves to site_config.json.
"""
import frappe
import json


@frappe.whitelist(allow_guest=True)
def oauth_callback():
    """
    Handles the Shopify OAuth redirect:
    GET /api/method/erpops.shopify.oauth_callback?code=xxx&state=yyy
    Exchanges code for access token, saves to site_config.json, redirects to success page.
    """
    import urllib.request
    import urllib.parse

    code = frappe.request.args.get("code", "")
    state = frappe.request.args.get("state", "")
    shop = frappe.request.args.get("shop", "")
    if not shop:
        frappe.respond_as_web_page(
            "Shopify OAuth Error",
            "<h3>No shop domain received</h3>",
            http_status_code=400
        )
        return

    if not code:
        frappe.respond_as_web_page(
            "Shopify OAuth Error",
            "<h3>No code received</h3><p>Query: " + str(dict(frappe.request.args)) + "</p>",
            http_status_code=400
        )
        return

    import os
    client_id = getattr(frappe.conf, "shopify_client_id", "") or os.environ.get("SHOPIFY_CLIENT_ID", "")
    client_secret = getattr(frappe.conf, "shopify_client_secret", "") or os.environ.get("SHOPIFY_CLIENT_SECRET", "")

    # Exchange code for token
    post_data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
    }).encode()

    req = urllib.request.Request(
        f"https://{shop}/admin/oauth/access_token",
        data=post_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    try:
        with urllib.request.urlopen(req) as r:
            result = json.loads(r.read())
    except Exception as e:
        frappe.respond_as_web_page(
            "Token Exchange Failed",
            f"<h3>Error</h3><p>{e}</p>",
            http_status_code=500
        )
        return

    token = result.get("access_token", "")
    if not token:
        frappe.respond_as_web_page(
            "No Token",
            f"<h3>No token in response</h3><pre>{result}</pre>",
            http_status_code=500
        )
        return

    # Save token to site_config.json
    site_config_path = frappe.get_site_path("site_config.json")
    with open(site_config_path) as f:
        cfg = json.load(f)
    cfg["shopify_access_token"] = token
    cfg["shopify_domain"] = shop
    with open(site_config_path, "w") as f:
        json.dump(cfg, f, indent=1)

    # Log it
    frappe.logger().info(f"Shopify token saved for shop: {shop}")

    # Automatically register webhook subscriptions using the dynamic host URL
    try:
        scheme = frappe.local.request.headers.get("X-Forwarded-Proto") or "https"
        host_url = f"{scheme}://{frappe.local.request.host}"
        
        # Temporary set context so ShopifyClient can authenticate immediately
        frappe.conf.shopify_access_token = token
        frappe.conf.shopify_domain = shop
        
        from erpops.erpops.shopify.shopify_client import ShopifyClient
        client = ShopifyClient()
        client.register_webhooks(host_url)
    except Exception as e:
        frappe.logger().error(f"Failed to auto-register webhooks: {e}")

    frappe.respond_as_web_page(
        "Shopify Connected",
        f"""
        <div style="font-family:sans-serif;padding:40px;text-align:center;max-width:600px;margin:auto">
        <h2 style="color:#2ecc71">Shopify connected!</h2>
        <p>Access token saved to ERPNext configuration.</p>
        <p style="color:#888;font-size:12px">Token: {token[:20]}...{token[-6:]}</p>
        <p><a href="/app/erpops_dashboard">Return to ErpOps dashboard</a></p>
        </div>
        """,
        http_status_code=200
    )
