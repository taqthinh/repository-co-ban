# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Shopify App',
    'version' : '1.1',
    'summary': 'Shopify App',
    'sequence': 5,
    'description': """
    """,
    'category': '',
    'website': '',
    'images' : [''],
    'depends' : ['base', 'mail', 'l10n_vn'],
    'data': [
        'security/ir.model.access.csv',
        'views/shopify_controller.xml',
        'views/shopify_store_views.xml',
        'views/xero_account_views.xml',
    ],
    'demo': [

    ],
    'qweb': [

    ],
    'css': ['static/src/css/shopify_app.css'],
    'installable': True,
    'application': True,
    'auto_install': False,

}
