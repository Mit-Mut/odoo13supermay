# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class ChangeDetector(models.TransientModel):
    _name = 'change_detector'
    _description = 'detector of changes in DB'

    def broadcast(self, message):
        print(self._cr.dbname)
        self.env['bus.bus'].sendone((self._cr.dbname, 'change_detector'), message)


class Product(models.Model):
    _inherit = 'product.index'
    _description = 'it saves index for changes in products' 

    @api.model
    def create(self, vals):
        res = super(Product, self).create(vals)
        self.env['change_detector'].broadcast({'p': res.id})
        return res

    @api.model
    def sync_not_reload(self, client_version=0, _fields=None):
        all_changed = self.search([('id', '>', client_version)])

        updated = ''
        created = ''
        deleted = ''

        for o in all_changed:
            updated = updated + ',' + o.updated if o.updated else updated
            created = created + ',' + o.created if o.created else created
            deleted = deleted + ',' + o.deleted if o.deleted else deleted

        update_ids = [int(x) for x in updated.split(',') if x.isdigit()]
        create_ids = [int(x) for x in created.split(',') if x.isdigit()]
        delete_ids = [int(x) for x in deleted.split(',') if x.isdigit()]

        disable_in_pos = self.env['product.product'].search([('id', 'in', update_ids), '|',
                                                             ('available_in_pos', '=', False),
                                                             ('active', '=', False)])
        disable_ids = [p.id for p in disable_in_pos]

        create_set = set(update_ids + create_ids)
        delete_set = set(delete_ids + disable_ids)

        _fields = [] if not _fields else _fields
        records = self.env['product.product'].with_context(display_default_code=False)\
            .search_read([('id', 'in', list(create_set - delete_set))], _fields)

        return {
            'create': records,
            'delete': list(delete_set),
            'latest_version': self.get_latest_version(client_version),
        }

    @api.model
    def get_real_qty(self,company_id,location_id):#, product_ids):
        #return ['gerardo']
        #product_ids = self.env['product.product'
        #_logger.warning(product_ids)
        stocks = self.env['stock.quant'].search([('company_id','=',company_id ),('location_id','=',location_id)])#,('product_id','in',product_ids)])
        result = {}
        for stock in stocks:
            result[stock.product_id.id]= stock.quantity-stock.reserved_quantity


        return result #stocks #[1] #self.env['product.product']#1 #stocks



class Customer(models.Model):
    _inherit = 'customer.index'
    _description = 'It saves the indexes for changes in customers'

    @api.model
    def create(self, vals):
        res = super(Customer, self).create(vals)
        self.env['change_detector'].broadcast({'c': res.id})
        return res

    @api.model
    def sync_not_reload(self, client_version=0, _fields=None):
        all_changed = self.search([('id', '>', client_version)])

        updated = ''
        created = ''
        deleted = ''

        for o in all_changed:
            updated = updated + ',' + o.updated if o.updated else updated
            created = created + ',' + o.created if o.created else created
            deleted = deleted + ',' + o.deleted if o.deleted else deleted

        update_ids = [int(x) for x in updated.split(',') if x.isdigit()]
        create_ids = [int(x) for x in created.split(',') if x.isdigit()]
        delete_ids = [int(x) for x in deleted.split(',') if x.isdigit()]

        disable_in_pos = self.env['res.partner'].search([('id', 'in', update_ids), '|',
                                                         ('customer', '=', False),
                                                         ('active', '=', False)])
        disable_ids = [p.id for p in disable_in_pos]

        create_set = set(update_ids + create_ids)
        delete_set = set(delete_ids + disable_ids)

        _fields = [] if not _fields else _fields
        records = self.env['res.partner'].search_read([('id', 'in', list(create_set - delete_set))], _fields)

        return {
            'create': records,
            'delete': list(delete_set),
            'latest_version': self.get_latest_version(client_version),
        }
