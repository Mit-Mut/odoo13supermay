# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
from datetime import datetime, date, time, timedelta

_logger = logging.getLogger(__name__)


class SmayReprintTocketOrderline(models.Model):
    _inherit = 'pos.order.line'

    x_descuento = fields.Float(string='Descuento aplicado al producto', default=0.0)


class SmayReprintTicketPosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def get_tickets_for_reprint(self):
        tickets = []
        today = datetime.now().replace(microsecond=0)

        config_ids = []
        '''for config_id in self.env.user.pos_config_ids:
            config_ids.append(config_id.id)'''

        config_ids.append(self.env['pos.session'].search(
            [('state', '=', 'opened'), ('user_id', '=', self.env.user.id)], limit=1).config_id.id)

        current_sesion = self.env['pos.session'].search(
            [('user_id', '=', self._uid), ('state', '=', 'opened'), ('config_id', 'in', config_ids)],
            order='id desc', limit=1)

        allowed_date = today - timedelta(days=current_sesion.config_id.days_of_reprint)
        orders = self.search([('id', '>', '0'), ('date_order', '>=', str(allowed_date)),
                              ('company_id.id', '=', self.env.user.company_id.id), ('config_id', 'in', config_ids)],
                             order='id desc')
        for order in orders:
            ticket = dict()
            ticket['id'] = order.id
            ticket['pos_reference'] = order.pos_reference
            ticket['date_order'] = order.date_order
            ticket['cashier'] = order.user_id.name
            # ticket['is_refund'] = order.is_refund
            ticket['amount_total'] = order.amount_total
            ticket['cliente'] = order.partner_id.name
            tickets.append(ticket)
        return tickets

    @api.model
    def get_information_reprint(self, order_id, recalculo_pzs):
        order = self.browse(int(order_id))
        ticket_to_reprint = dict()

        ticket_to_reprint['date_order'] = order.date_order  # self.get_correct_datetime(order.date_order)
        ticket_to_reprint['pos_reference'] = order.pos_reference
        ticket_to_reprint['cashier'] = order.user_id.name,
        ticket_to_reprint['partner'] = order.partner_id.name
        _order_lines = []
        taxes = dict()
        subtotal = 0
        qty_products = 0
        for orderline in self.env['pos.order.line'].search([('order_id', '=', order.id)]):
            qty_products = qty_products + orderline.qty
            _order_line = dict()
            _order_line['name_product'] = orderline.product_id.name
            _order_line['product_id'] = orderline.product_id.id
            _order_line['qty'] = orderline.qty
            _order_line['price_unit'] = orderline.price_unit
            _order_line['discount'] = orderline.discount
            _order_line['descuento_smay'] = orderline.x_descuento

            for tax in orderline.tax_ids:
                if tax.amount > 0:
                    subtotal = subtotal + (orderline.price_unit * orderline.qty) / ((tax.amount / 100) + 1)
                    if not taxes.get(tax.id):
                        taxes[tax.id] = (orderline.price_unit * orderline.qty) - (
                                orderline.price_unit * orderline.qty) / ((tax.amount / 100) + 1)
                    else:
                        taxes.update({tax.id: taxes.get(tax.id) + (
                                orderline.price_unit * orderline.qty - (orderline.price_unit * orderline.qty) / ((
                                                                                                                         tax.amount / 100) + 1))})  # [tax.id] = taxes[tax.amount] #+ (((tax.amount/100)+1)*orderline.price_unit)
                else:
                    subtotal = subtotal + (orderline.price_unit * orderline.qty)  ##*orderline.price_unit*orderline.qty
            _order_lines.append(_order_line)
        payments = []
        _payment = {}
        for payment in order.payment_ids:
            _payment = {}
            if payment.amount > 0 and order.amount_total > 0:
                _payment['name'] = payment.payment_method_id.name
                _payment['amount'] = payment.amount
                payments.append(_payment)
            if payment.amount < 0 and order.amount_total < 0:
                _payment['name'] = payment.payment_method_id.name
                _payment['amount'] = payment.amount
                payments.append(_payment)
                # _payment[statement.journal_id.name] = statement.amount

        ticket_to_reprint['orderlines'] = _order_lines
        ticket_to_reprint['subtotal'] = subtotal
        ticket_to_reprint['taxes'] = taxes
        ticket_to_reprint['total'] = order.amount_total
        ticket_to_reprint['payments'] = payments
        ticket_to_reprint['change_amount'] = order.amount_return
        ticket_to_reprint['qty_products'] = qty_products
        ticket_to_reprint['x_bank_reference'] = order.x_bank_reference
        # ticket_to_reprint['is_refund'] = order.is_refund
        # for tax in
        return ticket_to_reprint
