from odoo import api, fields, models, _

class ShopifyStore(models.Model):
    _name = 'shopify.store'
    description = 'Shopify Store'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Store Name')
    partner_id = fields.Many2one('res.partner', string='Partner')
    shopify_token = fields.Char(string="Shopify Token")
    shopify_url = fields.Char(string="Shopify URL")