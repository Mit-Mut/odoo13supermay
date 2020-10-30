# -*- coding: utf-8 -*-

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    pos_config_ids = fields.Many2many('pos.config', string='Puntos de Venta disponbles',
                                      help="Puntos de Venta disponibles para el usuario. El encargado (Responsable) puede ver todos los puntos de venta.")
