from odoo import http
from odoo.http import request
from odoo.exceptions import UserError
import shopify
import werkzeug
import requests
import json
from .config import DefaultConfig

class XeroController(http.Controller):
    @http.route('/xero_connect', auth='public', type='http')
    def xero_connect(self, *ar, **kw):
        xero_config = DefaultConfig()
        client_id = xero_config.CLIENT_ID
        redirect_uri = xero_config.BASE_URL+'/xero/callback'
        scope = 'openid profile email'
        state = '123'
        redirect = xero_config.XERO_URL + '/identity/connect/authorize?response_type=code&client_id=%s&redirect_uri=%s&scope=%s&state=%s'%(client_id,redirect_uri,scope,state)

        return werkzeug.utils.redirect(redirect)

    @http.route('/xero/callback', auth='public', type='http')
    def xero_callback(self, *ar, **kw):
        print('abc')
