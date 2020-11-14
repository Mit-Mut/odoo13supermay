# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, Warning, ValidationError
import logging

_logger = logging.getLogger(__name__)


class PosInvoicePosOrder(models.Model):
    _inherit = 'pos.config'

    x_cuenta_analitica = fields.Many2one('account.analytic.account', string='Cuenta Analitica',
                                         help='Asigna la cuenta analitica a las facturas generadas con el punto de venta.')
