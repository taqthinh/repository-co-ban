from odoo import api, fields, models, _

class ShopifyStore(models.Model):
    _name = 'shopify.store'
    description = 'Shopify Store'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Store Name')
    partner_id = fields.Many2one('res.partner', string='Partner')
    shopify_token = fields.Char(string="Shopify Token")
    shopify_url = fields.Char(string="Shopify URL")
    xero_token = fields.Text(string="Xero Token")

    sale_account = fields.Char(string="Xero Sale Account")
    shipping_account = fields.Char(string="Xero Shipping Account")
    payment_account = fields.Char(string="Xero Payment Account")
    auto_sync = fields.Boolean(string='Automatically Sync')

class XeroAccount(models.Model):
    _name = 'xero.account'
    _description = 'Xero Accounts'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'code'

    name = fields.Char('Account Name')
    code = fields.Char('Account Code')
    type = fields.Char('Account Type')
    # active = fields.Boolean(default=True)
