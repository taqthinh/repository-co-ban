import os

class XeroConfig(object):

    BASE_URL = "https://odoo.website"
    CALLBACK_URL = "https://odoo.website/xero/callback"
    XERO_URL = "https://login.xero.com"
    XERO_OAUTH2_TOKEN_URL = "https://identity.xero.com/connect/token"
    XERO_SCOPE = "offline_access openid profile email accounting.transactions accounting.contacts accounting.settings"
    # XERO_SCOPE = "accounting.contacts.read offline_access accounting.transactions.read"

    CLIENT_ID = "03CBCCCF06BD427D8D85B2F71EA075D3"
    CLIENT_SECRET = "vkosbjeHMfQ7Wa38JCUVzTyadlMIw7Pzr1WnW6m0FE0hViLy"