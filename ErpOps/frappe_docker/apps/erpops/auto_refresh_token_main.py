import os
import urllib.request
import urllib.parse
import json
import time
import frappe

# Dynamically resolve site name and sites folder path relative to script location
script_dir = os.path.dirname(os.path.abspath(__file__))
site_name = os.path.basename(script_dir)
sites_dir = os.path.dirname(script_dir)

# Initialize Frappe framework context
frappe.init(site=site_name, sites_path=sites_dir)
frappe.connect()

# Read Shopify credentials securely from site_config.json
client_id = frappe.conf.shopify_client_id
client_secret = frappe.conf.shopify_client_secret
shop = frappe.conf.shopify_domain

def get_token():
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
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["access_token"]

def update_erpnext(token):
    # Update Shopify Setting directly via Frappe DB
    doc = frappe.get_doc("Shopify Setting", "Shopify Setting")
    doc.password = token
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    print(f"Token updated: {token[:20]}...")

while True:
    try:
        token = get_token()
        update_erpnext(token)
    except Exception as e:
        print("Error:", e)
    time.sleep(82800)  # refresh every 23 hours
