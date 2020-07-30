from odoo import http
from odoo.http import request
from odoo.exceptions import UserError
import shopify
import werkzeug
import requests
import json
from .shopify_config import ShopifyConfig
from urllib.parse import urlparse, parse_qs
from .xero import XeroController

class ShopifyController(http.Controller):

    # @http.route('/index', auth='public', type='http', csrf=False)
    # def index(self,*ar, **kw):
    #     shop_url = self.get_shop_url(kw=kw,request=request)
    #     if shop_url:
    #         request.session['shop_url'] = shop_url
    #         shopify_store = request.env['shopify.store'].sudo().search([('shopify_url', '=', shop_url)],limit=1)
    #         shopify_token = shopify_store.shopify_token
    #         if shopify_token:
    #             current_app = ShopifyConfig()
    #             shopify.Session.setup(api_key=current_app.SHOPIFY_API_KEY, secret=current_app.SHOPIFY_SHARED_SECRET)
    #             session = shopify.Session(shop_url, current_app.API_VERSION,shopify_token)
    #             shopify.ShopifyResource.activate_session(session)
    #
    #             shop = shopify.Shop.current()
    #             context = {
    #                 'shop':shop,
    #                 'shop_url': shop_url,
    #                 'shopify_store': shopify_store,
    #             }
    #             return request.render('shopify_app.index',context)


    def get_shopify(self,shop_url=None):
        # url = request.httprequest.referrer
        # shop_url = ''
        # if url:
        #     shop_url = urlparse(url)
        if not shop_url:
            shop_url = self.get_shop_url()
        if shop_url:
            shopify_token = request.env['shopify.store'].sudo().search([('shopify_url', '=', shop_url)],
                                                                limit=1).shopify_token
            if shopify_token:
                current_app = ShopifyConfig()
                shopify.Session.setup(api_key=current_app.SHOPIFY_API_KEY, secret=current_app.SHOPIFY_SHARED_SECRET)
                session = shopify.Session(shop_url, current_app.API_VERSION, shopify_token)
                shopify.ShopifyResource.activate_session(session)
                return shopify


    @http.route('/shopify', auth='public', type='http')
    def shopify(self,**kw):
        shop_url = kw['shop']
        current_app = ShopifyConfig()
        shopify.Session.setup(api_key=current_app.SHOPIFY_API_KEY, secret=current_app.SHOPIFY_SHARED_SECRET)
        session = shopify.Session(shop_url, current_app.API_VERSION)
        redirect_uri = current_app.CALLBACK_URL
        permission_url = session.create_permission_url(redirect_uri=redirect_uri, scope=current_app.SHOPIFY_SCOPE)
        return werkzeug.utils.redirect(permission_url)

    @http.route('/shopify/callback', auth='public', type='http')
    def shopify_callback(self, **kw):
        shop_url = kw['shop']
        current_app = ShopifyConfig()
        shopify.Session.setup(api_key=current_app.SHOPIFY_API_KEY, secret=current_app.SHOPIFY_SHARED_SECRET)
        session = shopify.Session(shop_url, current_app.API_VERSION)
        token = session.request_token(kw)
        shopify.ShopifyResource.activate_session(session)
        shop = shopify.Shop.current()
        state_id = request.env['res.country.state'].sudo().search([('name','ilike',shop.city)],limit=1)
        if not state_id:
            state_id = None
        country_id = request.env['res.country'].sudo().search([('name','ilike',shop.country_name)],limit=1)
        if not country_id:
            country_id = None
        partner_vals = {
            'is_company': True,
            'name': shop.name,
            'email': shop.email,
            'website': shop.domain,
            'street': shop.address1,
            'street2': shop.address2,
            'city': shop.province,
            'state_id': state_id.id,
            'country_id': country_id.id,
            'zip': shop.zip,
            'phone': shop.phone,
        }
        # remove 'http://'
        website = request.env['res.partner'].sudo()._clean_website(shop.domain)
        partner_existed = request.env['res.partner'].sudo().search([('website','=',website)],limit=1)
        if not partner_existed:
            partner_existed = request.env['res.partner'].sudo().create(partner_vals)
        else:
            partner_existed.sudo().write(partner_vals)
        store_vals = {
            'partner_id': partner_existed.id,
            'name': shop.name,
            'shopify_token': token,
            'shopify_url': shop_url,
        }
        store_existed = request.env['shopify.store'].sudo().search([('shopify_url','=',shop_url)],limit=1)
        if not store_existed:
            store_existed = request.env['shopify.store'].sudo().create(store_vals)
            partner_existed.sudo().write({'shopify_store_id':store_existed.id})
        else:
            store_existed.sudo().write(store_vals)
        return werkzeug.utils.redirect('/index?shop_url=%s'%shop_url)
        # return werkzeug.utils.redirect('/index2')

    @http.route('/customer_list', auth='public', type='http')
    def customer_list(self, *ar, **kw):
        shop_url = ''
        if 'shop_url' in kw:
            shop_url = kw['shop_url']
            request.params['shop_url'] = shop_url
            shopify = self.get_shopify()
            customers = shopify.Customer.find()
            if customers:
                context = {
                    'customers': customers,
                    'shop_url': shop_url,
                }
                return request.render('shopify_app.customer_list', context)

    def get_shop_url(self, kw=None):
        shop_url = ''
        if kw:
            if 'shop_url' in kw:
                shop_url = kw['shop_url']
        if request.httprequest.referrer:
            url = request.httprequest.referrer
            url_parse = ''
            if url:
                url_parse = urlparse(url)
                if 'shop_url' in parse_qs(url_parse.query):
                    shop_url = parse_qs(url_parse.query)['shop_url'][0]
        return shop_url

