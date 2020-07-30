import os

class ShopifyConfig(object):

    BASE_URL = "https://odoo.website"
    CALLBACK_URL = "https://odoo.website/shopify/callback"
    PREFERRED_URL_SCHEME = "https"
    SHOPIFY_SCOPE = [ "read_inventory","read_customers", "write_customers", "write_products", "read_products","write_price_rules" , "read_price_rules", "read_script_tags","read_discounts","write_discounts",
            "read_draft_orders" ,"write_script_tags", "read_orders", "read_checkouts",]
    SHOPIFY_API_KEY = '788e63f1080f4d1727401a31e33e2579'
    SHOPIFY_SHARED_SECRET = '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'
    API_VERSION = '2020-04'