# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

import logging

from odoo import models, fields, api, SUPERUSER_ID, _, http
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from pytz import timezone

from datetime import datetime, date, time, timedelta

_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = 'pos.config'

    enable_x_report = fields.Boolean('Habilitar el reporte Arqueo/Cierre', default=True)


class pos_session(models.Model):
    _inherit = 'pos.session'

    def get_user(self):
        if self._uid == SUPERUSER_ID:
            return True

    def get_payments(self):
        if self:
            self._cr.execute("""
                SELECT ppm.name,
                    sum(pp.amount) 
                FROM pos_payment pp 
                JOIN pos_payment_method ppm 
                ON pp.payment_method_id = ppm.id  
                WHERE session_id = %d 
                GROUP BY ppm.name order by 1 ;
            """ % (self))
            data = self._cr.dictfetchall()
            return data
        else:
            return {}

    def get_total_sales(self):
        total_price = 0.0
        if self:
            for order in self.order_ids:
                # _logger.debug(str(order.amount_total) + '   ' + str(order.amount_tax))
                if order.state != 'draft' and order.amount_total > 0:
                    total_price += sum([(line.qty * line.price_unit) for line in order.lines])
        return total_price - self.get_total_tax()

    def get_total_tax(self):
        total_tax = 0.0
        if self:
            pos_order_obj = self.env['pos.order']
            total_tax += sum([order.amount_tax for order in pos_order_obj.search(
                [('session_id', '=', self.id), ('state', '!=', 'draft'), ('amount_total', '>', 0)])])
        return total_tax

    def get_company_data(self):
        return self.user_id.company_id

    def get_current_date(self):
        if self._context and self._context.get('tz'):
            tz_name = self._context['tz']
        else:
            tz_name = self.env['res.users'].browse([self._uid]).tz
        if tz_name:
            tz = timezone(tz_name)
            c_time = datetime.now(tz)
            return c_time.strftime('%d/%m/%Y')
        else:
            return date.today().strftime('%d/%m/%Y')

    def get_session_date(self, date_time):
        if date_time:
            if self._context and self._context.get('tz'):
                tz_name = self._context['tz']
            else:
                tz_name = self.env['res.users'].browse([self._uid]).tz
            if tz_name:
                tz = timezone(tz_name)
                c_time = datetime.now(tz)
                hour_tz = int(str(c_time)[-5:][:2])
                min_tz = int(str(c_time)[-5:][3:])
                sign = str(c_time)[-6][:1]
                if sign == '+':
                    date_time = datetime.strptime(str(date_time), DEFAULT_SERVER_DATETIME_FORMAT) + \
                                timedelta(hours=hour_tz, minutes=min_tz)
                else:
                    date_time = datetime.strptime(str(date_time), DEFAULT_SERVER_DATETIME_FORMAT) - \
                                timedelta(hours=hour_tz, minutes=min_tz)
            else:
                date_time = datetime.strptime(str(date_time), DEFAULT_SERVER_DATETIME_FORMAT)
            return date_time.strftime('%d/%m/%Y')

    def get_current_time(self):
        if self._context and self._context.get('tz'):
            tz_name = self._context['tz']
        else:
            tz_name = self.env['res.users'].browse([self._uid]).tz
        if tz_name:
            tz = timezone(tz_name)
            c_time = datetime.now(tz)
            return c_time.strftime('%I:%M:%S %p')
        else:
            return datetime.now().strftime('%I:%M:%S %p')

    def get_session_time(self, date_time):
        if date_time:
            if self._context and self._context.get('tz'):
                tz_name = self._context['tz']
            else:
                tz_name = self.env['res.users'].browse([self._uid]).tz
            if tz_name:
                tz = timezone(tz_name)
                c_time = datetime.now(tz)
                hour_tz = int(str(c_time)[-5:][:2])
                min_tz = int(str(c_time)[-5:][3:])
                sign = str(c_time)[-6][:1]
                if sign == '+':
                    date_time = datetime.strptime(str(date_time), DEFAULT_SERVER_DATETIME_FORMAT) + \
                                timedelta(hours=hour_tz, minutes=min_tz)
                else:
                    date_time = datetime.strptime(str(date_time), DEFAULT_SERVER_DATETIME_FORMAT) - \
                                timedelta(hours=hour_tz, minutes=min_tz)
            else:
                date_time = datetime.strptime(str(date_time), DEFAULT_SERVER_DATETIME_FORMAT)
            return date_time.strftime('%I:%M:%S %p')

    def get_total_returns(self):
        pos_order_obj = self.env['pos.order']
        total_return = 0.0
        if self:
            for order in pos_order_obj.search([('session_id', '=', self.id)]):
                if order.amount_total < 0:
                    total_return += abs(order.amount_total)
        return total_return

    def get_total_discount(self):
        total_discount = 0.0
        if self and self.order_ids:
            for order in self.order_ids:
                total_discount += sum([((line.qty * line.price_unit) * line.discount) / 100 for line in order.lines])
        return total_discount

    def get_total_first(self):
        global gross_total
        if self:
            gross_total = (self.get_total_sales() + self.get_total_tax()) \
                          - self.get_total_returns()  # + self.get_total_discount()
        return gross_total

    #  Super May's functions

    def get_thousands_format(self, quantity):
        return '{0:,.2f}'.format(quantity)

    def get_total_tickets(self):
        return self.order_count

    def get_retirements(self):
        retirements = self.env['account.bank.statement.line'].search(
            [('ref', '=', self.name), ('name', 'in', ['retiro', 'gasto', 'prestamo'])],
            order='sequence_cashbox_out_id asc')
        retirements_data = []
        for retirement in retirements:
            ret = {}
            ret['id_retirement'] = retirement.sequence_cashbox_out_id
            ret['amount'] = abs(retirement.amount)
            ret['motivo'] = retirement.name
            ret['comment'] = retirement.comment
            retirements_data.append(ret)
        return retirements_data

    def status_session(self):
        return self.state

    def get_orders_with_reference(self):
        for session in self:
            order_references = self.env['pos.order'].search(
                [('session_id', '=', session.id), ('x_bank_reference', '!=', ''),
                 ('amount_total', '>', '0'),
                 ('state', 'in', ['paid', 'invoiced', 'done'])])

        if order_references:
            orders = []
            ord = {}
            for order in order_references:
                ord['pos_reference'] = order.pos_reference.replace('Order ', '').replace('Pedido ', '').replace(
                    'Orden ', '')
                metodo = {}
                metodos = []
                for met in order.payment_ids:
                    metodo['metodo'] = met.payment_method_id.name.split()[0]
                    metodo['monto'] = 0
                    if met.amount > 0:
                        metodo['monto'] = met.amount
                    metodos.append(metodo)
                    metodo = {}
                ord['metodos'] = metodos
                ord['total'] = order.amount_total
                orders.append(ord)
                ord = {}
            return orders
        else:
            return {}

    '''def get_product_category(self):
        product_list = []
        if self and self.order_ids:
            for order in self.order_ids:
                for line in order.lines:
                    flag = False
                    product_dict = {}
                    for lst in product_list:
                        if line.product_id.pos_categ_id:
                            if lst.get('pos_categ_id') == line.product_id.pos_categ_id.id:
                                lst['price'] = lst['price'] + (line.qty * line.price_unit)
                                flag = True
                        else:
                            if lst.get('pos_categ_id') == '':
                                lst['price'] = lst['price'] + (line.qty * line.price_unit)
                                flag = True
                    if not flag:
                        product_dict.update({
                            'pos_categ_id': line.product_id.pos_categ_id and line.product_id.pos_categ_id.id or '',
                            'price': (line.qty * line.price_unit)
                        })
                        product_list.append(product_dict)
        return product_list'''

    '''def get_gross_total(self):
        total_cost = 0.0
        gross_total = 0.0
        if self and self.order_ids:
            for order in self.order_ids:
                if order.state != 'draft':
                    for line in order.lines:
                        total_cost += line.qty * line.product_id.standard_price
            gross_total = self.get_total_sales() - \
                          + self.get_total_tax() - total_cost
        return gross_total'''

    '''def get_product_cate_total(self):
        balance_end_real = 0.0
        if self and self.order_ids:
            for order in self.order_ids:
                if order.state != 'draft':
                    for line in order.lines:
                        balance_end_real += (line.qty * line.price_unit)
        return balance_end_real'''

    '''def get_net_gross_total(self):
        net_gross_profit = 0.0
        total_cost = 0.0
        if self and self.order_ids:
            for order in self.order_ids:
                if order.state != 'draft':
                    for line in order.lines:
                        total_cost += line.qty * line.product_id.standard_price
            net_gross_profit = self.get_total_sales() - self.get_total_tax() - total_cost
        return net_gross_profit'''

    '''def get_product_name(self, category_id):
        if category_id:
            category_name = self.env['pos.category'].browse([category_id]).name
            return category_name'''

    '''def get_url_session_barcode(self):
        # return 'http://localhost:8069/report/barcode/Code128/' + str(self.name).replace('POS/', '')
        return str(
            http.request.env['ir.config_parameter'].get_param('web.base.url')) + '/report/barcode/Code128/' + str(
            self.name).replace('POS/', '')'''
