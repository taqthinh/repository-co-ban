from odoo import http
from odoo.http import request
from odoo.exceptions import UserError
import werkzeug
import requests
import json
import maya
from .shopify import ShopifyController
from .xero import XeroController
import timeit
from profilehooks import profile
from datetime import datetime, timedelta


class MainController(http.Controller):

    @http.route('/index', auth='public', type='http', csrf=False)
    def index(self, *ar, **kw):
        shop_url = ShopifyController().get_shop_url(kw=kw)
        if shop_url:
            request.session['shop_url'] = shop_url
            shopify_store = request.env['shopify.store'].sudo().search([('shopify_url', '=', shop_url)], limit=1)
            accounts = request.env['xero.account'].sudo().search([])
            if shopify_store:
                context = {
                    'shop_url': shop_url,
                    'shopify_store': shopify_store,
                    'accounts': accounts,
                }
                return request.render('shopify_app.index', context)

    @http.route('/save_settings', auth='public', type='http', csrf=False)
    def save_settings(self, *ar, **kw):
        shop_url = ShopifyController().get_shop_url(kw=kw)
        if shop_url:
            shopify_store = request.env['shopify.store'].sudo().search([('shopify_url', '=', shop_url)])
            if shopify_store:
                sale_account = shopify_store.sale_account
                if 'sale_account' in kw:
                    sale_account = kw['sale_account']
                shipping_account = shopify_store.shipping_account
                if 'shipping_account' in kw:
                    shipping_account = kw['shipping_account']
                payment_account = shopify_store.payment_account
                if 'payment_account' in kw:
                    payment_account = kw['payment_account']
                # auto_sync = shopify_store.auto_sync
                if 'auto_sync' in kw:
                    auto_sync = True
                else:
                    auto_sync = False
                vals = {
                    'sale_account': sale_account,
                    'shipping_account': shipping_account,
                    'payment_account': payment_account,
                    'auto_sync': auto_sync,
                }
                shopify_store.sudo().write(vals)
                return werkzeug.utils.redirect('/index?shop_url=%s' % shop_url)

    @profile(immediate=True)
    @http.route('/sync_to_xero', auth='public', type='http', csrf=False)
    def sync_to_xero(self, *ar, **kw):
        shop_url = ShopifyController().get_shop_url(kw=kw)
        context = {}
        if shop_url:
            shopify_store = request.env['shopify.store'].sudo().search([('shopify_url', '=', shop_url)], limit=1)
            accounts = request.env['xero.account'].sudo().search([])
            if shopify_store:
                context = {
                    'shop_url': shop_url,
                    'shopify_store': shopify_store,
                    'accounts': accounts,
                }
        from_date = ''
        to_date = ''
        if 'from_date' in kw:
            from_date = kw['from_date']
        if 'to_date' in kw:
            to_date = kw['to_date']
        date_valid = self.is_date_valid(from_date,to_date)
        if not date_valid:
            context_error = {
                'message': 'Error: Invalid date'}
            context.update(context_error)
            return request.render('shopify_app.index',context)
        else:
            from_date ,to_date = self.convert_date_format(from_date=from_date,to_date=to_date)
            pass_contact = self.pass_contact_to_xero(from_date=from_date, to_date=to_date)
            if pass_contact:
                pass_product = self.pass_product_to_xero(from_date=from_date, to_date=to_date)
                if pass_product:
                    pass_order = self.pass_order_to_xero(from_date=from_date, to_date=to_date)
                    if pass_order:
                        return werkzeug.utils.redirect('/index?shop_url=%s'%shop_url)
                    else:
                        print('ERROR 3')
                else:
                    print('ERROR 2')
            else:
                print('ERROR 1')

    def switch_status(self, status):
        switcher = {
            'open': 'DRAFT',
            'invoice_sent': 'DRAFT',
            'pending': 'SUBMITTED',
            'authorized': 'AUTHORISED',
            'partially_paid': 'AUTHORISED',
            'paid': 'AUTHORISED',
            'partially_refunded': 'DELETED',
            'refunded': 'DELETED',
            'voided': 'DELETED',
        }
        return switcher.get(status,"DELETED")

    @http.route('/pass_contact_to_xero', auth='public', type='http')
    def pass_contact_to_xero(self, from_date, to_date, **kw):
        shopify = ShopifyController().get_shopify()
        vals_list = []
        if shopify:
            customers = shopify.Customer.find(updated_at_min=from_date, updated_at_max=to_date)
            # customers2 = shopify.Customer.find(updated_at_min='2020-07-18', updated_at_max='2020-07-20')
            if customers:
                vals_list = self.customer_vals_list(customers)
                xero = XeroController().get_xero()
                xero.contacts.save(vals_list)
                return True

    def customer_vals_list(self,customers):
        vals_list = []
        for customer in customers:
            vals = {
                "Name": '%s %s - Shopify (%s)' % (customer.first_name, customer.last_name, customer.id),
                "ContactNumber": customer.id,
                "IsSupplier": False,
                "IsCustomer": True,
                "FirstName": customer.first_name,
                "LastName": customer.last_name,
                "EmailAddress": customer.email,
                # "Phones": customer.phone,
                "ContactPersons": [
                    {
                        "FirstName": customer.first_name,
                        "LastName": customer.last_name,
                        "EmailAddress": customer.email,
                        "IncludeInEmails": True,
                    }
                ],
                "Phones": [
                    {
                        "PhoneType": "DEFAULT",
                        "PhoneNumber": customer.phone,
                    }, {
                        "PhoneType": "FAX"
                    }, {
                        "PhoneType": "MOBILE"
                    }, {
                        "PhoneType": "DDI"
                    }
                ],
            }
            vals_list.append(vals)
        return vals_list

    @http.route('/pass_product_to_xero', auth='public', type='http')
    def pass_product_to_xero(self, from_date, to_date, **kw):
        shop_url = ShopifyController().get_shop_url()
        if shop_url:
            shopify = ShopifyController().get_shopify(shop_url)
            vals_list = []
            if shopify:
                products = shopify.Product.find(updated_at_min=from_date, updated_at_max=to_date)
                # get product sale_account
                if products:
                    shopify_store = request.env['shopify.store'].sudo().search([('shopify_url', '=', shop_url)])
                    sale_account = ''
                    if shopify_store:
                        sale_account = shopify_store.sale_account
                    for product in products:
                        for variant in product.variants:
                            # item_cost = self.get_item_cost(inventory_items,variant )
                            vals = self.product_vals(product, variant, sale_account)
                            vals_list.append(vals)
                    xero = XeroController().get_xero()
                    xero.items.save(vals_list)
                    return True

    def get_item_cost(self,inventory_items, variant):
        item_cost = [inventory_item.cost for inventory_item in inventory_items if inventory_item.id == variant.inventory_item_id]
        result = 0
        if item_cost:
            result = int(item_cost[0])
        return result

    def product_vals(self,product, variant, sale_account):
        varitant_title = variant.title
        if varitant_title == 'Default Title':
            varitant_title = ''
        vals = {
            "Code": variant.id,
            "Name": product.title + ' ' + varitant_title.upper(),
            "Description": product.title + ' ' + varitant_title.upper(),
            # "PurchaseDescription": product.title + ' ' + varitant_title.upper(),
            # "PurchaseDetails": {
            #     "UnitPrice": item_cost,
            #     "COGSAccountCode": "300",
            #     "TaxType": "NONE"
            # },
            "SalesDetails": {
                "UnitPrice": int(variant.price),
                "AccountCode": sale_account,
                # "TaxType": "NONE"
            },
            "QuantityOnHand": variant.inventory_quantity,
            # "InventoryAssetAccountCode": "630",
            "IsSold": True,
            # "IsPurchased": True,
        }
        return vals

    # @profile(immediate=True)
    @http.route('/pass_order_to_xero', auth='public', type='http')
    def pass_order_to_xero(self, from_date, to_date, **kw):
        shop_url = ShopifyController().get_shop_url()
        if shop_url:
            shopify_store = request.env['shopify.store'].sudo().search([('shopify_url', '=', shop_url)])
            sale_account = ''
            shipping_account = ''
            payment_account = ''
            if shopify_store:
                sale_account = shopify_store.sale_account
                shipping_account = shopify_store.shipping_account
                payment_account = shopify_store.payment_account

            shopify = ShopifyController().get_shopify(shop_url)
            if shopify:
                vals_list = []
                orders = shopify.Order.find(updated_at_min=from_date, updated_at_max=to_date)
                if orders:
                    for order in orders:
                        # order vals
                            # add contact
                        vals = self.order_vals(order)
                        contact_vals = self.add_contact_vals(order)
                        if contact_vals:
                            vals['Contact'] = contact_vals
                            # add payment
                        # payment_vals = []
                        # if order.financial_status in ['paid', 'partially_paid']:
                        # # if order.financial_status in ['invoice_sent', 'pending']:
                        #     if shopify_store:
                        #         if order.payment_details:
                        #             payment_vals = [{
                        #                 "Amount": 1000,
                        #                 'Account': {
                        #                     'Code': shopify_store.payment_account
                        #                 },
                        #                 "Reference": "Naswm chawsc anw langw nes"
                        #             }]
                        #             vals['Payments'] = payment_vals

                        # order line vals
                            # add free ship ,discount amount item
                        line_items_vals = []
                        if order.discount_applications:
                            for discount_application in order.discount_applications:
                                if order.discount_codes:
                                    for discount_code in order.discount_codes:
                                        if discount_application.target_selection == 'all' or discount_application.target_selection == 'entitled':
                                            if discount_code.type == 'shipping':
                                                free_ship_item_vals = self.add_free_ship_item(order, sale_account)
                                                line_items_vals.append(free_ship_item_vals)
                                            elif discount_code.type == 'fixed_amount':
                                                fixed_amount_vals = self.add_discount_amount(order, sale_account)
                                                line_items_vals.append(fixed_amount_vals)
                                            elif discount_code.type == 'percentage':
                                                percentage_amount_vals = self.add_discount_percentage(order, sale_account)
                                                line_items_vals.append(percentage_amount_vals)
                                else:
                                    if discount_application.type == 'automatic':
                                        if discount_application.target_selection == 'all' or discount_application.target_selection == 'entitled':
                                            if discount_application.allocation_method == 'across':      # differ with buy 1 get 1
                                                if discount_application.value_type == 'fixed_amount':
                                                    auto_discount_fixed_vals = self.auto_discount_fixed(order, sale_account)
                                                    line_items_vals.append(auto_discount_fixed_vals)
                                                elif discount_application.value_type == 'percentage':
                                                    auto_discount_percentage_vals = self.auto_discount_percentage(order, sale_account)
                                                    line_items_vals.append(auto_discount_percentage_vals)

                            # Add shipping fee
                        if order.shipping_lines:
                            shipping_item_vals = self.add_shiping_item(order,shipping_account)
                            line_items_vals.append(shipping_item_vals)

                        for line_item in order.line_items:
                            discount_amount = 0
                            if line_item.total_discount:
                                discount_amount = discount_amount + int(line_item.total_discount)
                            line_vals = self.order_line_vals(line_item, discount_amount, sale_account)
                            line_items_vals.append(line_vals)
                        vals['LineItems'] = line_items_vals
                        vals_list.append(vals)
                    xero = XeroController().get_xero()
                    if xero:
                        xero.invoices.save(vals_list)
                        return True

    def order_vals(self, order):
        status = ''
        if order.financial_status:
            status = self.switch_status(order.financial_status)
        # get duedate
        duedate = maya.parse(order.created_at).datetime()
        vals = {
            "Type": "ACCREC",
            "DateString": order.created_at,
            "DueDate": duedate,
            "InvoiceNumber": "IVN:" + str(order.number),
            "Reference": order.name,
            "CurrencyCode": order.presentment_currency,
            "Status": 'AUTHORISED',
            "LineAmountTypes": "Inclusive" if order.taxes_included else "Exclusive",
            "SubTotal": order.subtotal_price,
            "TotalTax": order.total_tax,
            "Total": order.total_price,
            "Payments": [
                {
                    "Amount": "1000.00",
                    'Account': {
                        'Code': '201'
                    },
                    "Reference": "Naswm chawsc anw langw nes"
                }
            ],
        }
        return vals

    def order_line_vals(self, line_item, discount_amount, sale_account):
        line_vals = {
            "Description": line_item.name,
            "UnitAmount": int(line_item.price),
            "DiscountAmount": discount_amount,
            "ItemCode": line_item.variant_id,
            "Quantity": line_item.quantity,
            "TaxAmount": line_item.tax_lines[0].price,
            "AccountCode": sale_account,
            # "DiscountRate": DiscountRate,
        }
        return line_vals

    def add_contact_vals(self, order):
        contact_vals = {}
        if 'customer' in order.attributes:
            contact_vals = {
                "ContactNumber": order.customer.id,
            }
        else:
            contact_vals = {
                "ContactNumber": order.user_id,
                "Name": 'Shopify User: '+order.user_id
            }
        return contact_vals

    def add_shiping_item(self, order, shipping_account):
        shipping_item_vals = {
            "Description": 'Shipping: ' + order.shipping_lines[0].title,
            "UnitAmount": order.shipping_lines[0].price,
            "Quantity": 1,
            "AccountCode": shipping_account,
        }
        return shipping_item_vals

    def add_free_ship_item(self, order, sale_account):
        free_ship_item_vals = {
            "Description": "Free Ship",
            "UnitAmount": str(-int(order.discount_codes[0].amount)),
            "Quantity": 1,
            "TaxType": "NONE",
            "AccountCode": sale_account,
        }
        return free_ship_item_vals

    def add_discount_amount(self, order, sale_account):
        fixed_amount_vals = {
            "Description": "Discount Code: Fixed Amount",
            "UnitAmount": str(-int(order.discount_codes[0].amount)),
            "Quantity": 1,
            "TaxType": "NONE",
            "AccountCode": sale_account,
        }
        return fixed_amount_vals

    def add_discount_percentage(self, order, sale_account):
        percentage_amount_vals = {
            "Description": "Discount Code: Percentage",
            "UnitAmount": str(-int(order.discount_codes[0].amount)),
            "Quantity": 1,
            "TaxType": "NONE",
            "AccountCode": sale_account,
        }
        return percentage_amount_vals

    def auto_discount_fixed(self, order, sale_account):
        auto_discount_vals = {
            "Description": "Auto Discount Amount",
            "UnitAmount": str(-int(order.total_discounts)),
            "Quantity": 1,
            "TaxType": "NONE",
            "AccountCode": sale_account,
        }
        return auto_discount_vals

    def auto_discount_percentage(self, order, sale_account):
        auto_discount_vals = {
            "Description": "Auto Discount Pecentage",
            "UnitAmount": str(-int(order.total_discounts)),
            "Quantity": 1,
            "TaxType": "NONE",
            "AccountCode": sale_account,
        }
        return auto_discount_vals

    def is_date_valid(self,from_date,to_date):
        date_format = "%m/%d/%Y"
        a = datetime.strptime(from_date, date_format)
        b = datetime.strptime(to_date, date_format)
        delta = b - a
        if delta.days < 0:
            return False
        else:
            return True

    def convert_date_format(self, from_date, to_date):
        date_format = "%m/%d/%Y"
        from_date = datetime.strptime(from_date, date_format)
        from_date = from_date.strftime('%Y-%m-%d')
        to_date = datetime.strptime(to_date, date_format)
        # add 1 more day to to_date for call api
        to_date += timedelta(days=1)
        to_date = to_date.strftime('%Y-%m-%d')
        return from_date,to_date

    # start = timeit.timeit()
    # end = timeit.timeit()
    # print("Time: "+ str(end - start))