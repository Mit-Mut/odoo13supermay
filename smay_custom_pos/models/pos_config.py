# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = 'pos.config'

    fondo_caja = fields.Float(string="Fondo de Caja", default=500.00,
                              help="Se indica la cantidad que se tiene que manejar"
                                   " como fondo de caja.")
    sucursal_id = fields.Many2one('res.partner', string='Sucursal(ticket)',
                                  help="Selecciona la tienda que se presentara en el ticket")

    @api.model
    def existe_conexion(self):
        return True

    def open_session_cb(self):
        if self.user_has_groups('point_of_sale.group_pos_user') and self.env.user.partner_id.name.upper() != 'CHECADOR':
            sessions = self.env['pos.session'].search(
                [('user_id', '=', self.env.user.id), ('state', '!=', 'closed'), ('config_id', '!=', self.id)])
            for session in sessions:
                raise UserError('Ya tienes sesión abierta en el punto de venta: ' + session.config_id.name)
            if not self.env.user.sucursal_id:
                raise UserError('No puedes abrir el punto de venta porque no tienes sucursal asignada')
            if self.env.user.sucursal_id.id != self.sucursal_id.id:
                raise UserError(
                    'No puedes abrir el punto de venta porque pertenece a otra sucursal. Tu sucursal asignada es ' + str(
                        self.env.user.sucursal_id.name) + ' y del punto de venta ' + str(self.sucursal_id.name))
        return super(PosConfig, self).open_session_cb()
