# ErpOps

Custom ERPNext app for Shopify sync and operational alerts.

## How to Install
1. Expose local port `8080` (e.g. `ngrok http 8080`).
2. Set `localtunnel_url` in site configuration.
3. Configure **Shopify Settings** in ERPNext to auto-register webhooks.

## Core Features
- **Shopify Client**: Interacts with Shopify Admin API.
- **Marketplace Alerts**: Tracks stock/shipment issues.
- **Reorder Policy**: Manages SKU reorder points.
- **Webhooks**: Handles Shopify events.
