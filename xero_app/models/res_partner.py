from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    shopify_store_id = fields.Many2one('shopify.store', string='Shopify Store')