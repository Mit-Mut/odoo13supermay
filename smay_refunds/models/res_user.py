# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo import exceptions
import logging

_logger = logging.getLogger(__name__)


class SmayRefundResUser(models.Model):
    _inherit = 'res.users'

    is_manager = fields.Boolean(string='Es encargado', default=False)
    pos_security_pin = fields.Char(string='PIN para punto de venta')

    _sql_constraints = [
        ('pos_security_pin_uniq', 'unique(pos_security_pin)',
         "El PIN ingresado ya esta siendo utilizado por otro usuario.")]
    # sucursal_id = fields.Many2one('res.partner', string='Sucursal',
    #                                help="Seleciona la tienda que se presentara en el ticket")
