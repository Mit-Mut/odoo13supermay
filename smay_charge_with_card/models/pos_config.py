# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SmayChargeWithCard(models.Model):
    _inherit = 'pos.config'

    extra_charge = fields.Float(string="Porcentaje extra al pagar con tarjeta ", default=3.00,
                                help="Define que porcentaje sera añadido al pagar con tarjeta.")


class SmayChargeWithCardPosOrder(models.Model):
    _inherit = 'pos.order'

    x_bank_reference = fields.Char(string='Referencia Bancaria', readonly=True)

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(SmayChargeWithCardPosOrder, self)._order_fields(ui_order)
        order_fields['x_bank_reference'] = ui_order['x_bank_reference'] if ui_order.get('x_bank_reference') else ''
        return order_fields


class SmayChargeWithCardPosPayment(models.Model):
    _inherit = 'pos.payment.method'

    uso_terminal_smay = fields.Boolean(string='Cobro de comisión por uso de terminal',
                                       help='Se cobra la comision por el uso de la terminal bancaria', default=False)
