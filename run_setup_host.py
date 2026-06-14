import os
import urllib.request
import urllib.parse
import json

def read_env():
    env_path = os.path.join("ErpOps", "frappe_docker", ".env")
    if not os.path.exists(env_path):
        env_path = os.path.join("frappe_docker", ".env")
        if not os.path.exists(env_path):
            env_path = ".env"
            
    client_id = None
    client_secret = None
    shopify_shop = None
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("SHOPIFY_CLIENT_ID="):
                    client_id = line.split("=", 1)[1].strip()
                elif line.startswith("SHOPIFY_CLIENT_SECRET="):
                    client_secret = line.split("=", 1)[1].strip()
                elif line.startswith("SHOPIFY_SHOP="):
                    shopify_shop = line.split("=", 1)[1].strip()
    return client_id, client_secret, shopify_shop

def main():
    client_id, client_secret, shop = read_env()
    if not shop:
        shop = "ddfhhg-ae.myshopify.com"
        
    erpnext_url = "http://localhost:8080"
    erpnext_user = "Administrator"
    erpnext_pass = "admin"

    print("--- Host Shopify Setup ---")
    print(f"Reading credentials from .env...")
    print(f"Client ID: {client_id}")
    print(f"Shop URL: {shop}")

    if not client_id or not client_secret:
        print("Error: Could not read SHOPIFY_CLIENT_ID or SHOPIFY_CLIENT_SECRET from .env file!")
        return

    # 1. Fetch access token from Shopify
    print("Fetching Shopify Access Token...")
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
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read())
            token = res["access_token"]
            print("Successfully obtained access token!")
    except Exception as e:
        print(f"Error fetching token: {e}")
        print("Please check your .env credentials and verify the app is installed on your shop.")
        return

    # 2. Login to ERPNext and Update setting
    print("Updating ERPNext Shopify Setting...")
    try:
        # Login
        login_data = urllib.parse.urlencode({
            "usr": erpnext_user, "pwd": erpnext_pass
        }).encode()
        
        cookie_processor = urllib.request.HTTPCookieProcessor()
        opener = urllib.request.build_opener(cookie_processor)
        
        # Test login
        opener.open(f"{erpnext_url}/api/method/login", login_data)
        
        # Update Shopify Setting resource
        update_data = json.dumps({
            "enable_shopify": 1,
            "shopify_url": shop,
            "password": token
        }).encode()
        
        # In Frappe REST API, singletons are accessed by resource name / name
        req_put = urllib.request.Request(
            f"{erpnext_url}/api/resource/Shopify Setting/Shopify Setting",
            data=update_data,
            method="PUT",
            headers={"Content-Type": "application/json"}
        )
        
        with opener.open(req_put) as resp_put:
            print(resp_put.read().decode())
            print("Successfully updated ERPNext database!")
            
    except Exception as e:
        print(f"Error updating ERPNext: {e}")

if __name__ == "__main__":
    main()
