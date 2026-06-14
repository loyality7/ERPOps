# ERPOps

A lightweight, automated integration between ERPNext (v15) and Shopify.

## Key Features

*   **GraphQL Shopify Client:** Syncs orders, products, inventory, and pricing with automatic rate-limit backoff.
*   **Inbound Webhooks:** Dynamic synchronization of Shopify events (create, paid, cancel, fulfill, refund) with HMAC validation.
*   **Operational Dashboard:** Real-time KPIs, inventory velocity tracker, reorder workflows, and a natural language QA assistant (ask_erpops).
*   **Token Refresh:** Automated daemon to rotate session credentials.

## Project Structure

*   `ErpOps/frappe_docker/` - Containerized multi-app ERPNext local deployment.
*   `ErpOps/frappe_docker/apps/erpops/` - Custom Frappe backend/frontend code.
*   `auto_refresh_token.py` - Automated token refresh worker.

## Quick Setup

1.  **Configure .env**:
    Copy `.env.example` to `ErpOps/frappe_docker/.env` and fill in your Shopify credentials.
2.  **Start Services**:
    ```bash
    docker compose -f ErpOps/frappe_docker/pwd-custom.yml up -d
    ```
