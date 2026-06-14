import frappe
from ecommerce_integrations.shopify.product import ShopifyProduct
from ecommerce_integrations.shopify.connection import temp_shopify_session


@temp_shopify_session
def run():
    from shopify.resources import Product
    products = Product.find()
    print("Found products:", [p.id for p in products])
    for p in products:
        try:
            sp = ShopifyProduct(p.id)
            print("Syncing product:", p.id)
            sp.sync_product()
            print("Sync Success!")
        except Exception as e:
            import traceback
            traceback.print_exc()
