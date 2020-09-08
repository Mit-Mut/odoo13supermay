# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SmayCustomTicketResUser(models.Model):
    _inherit = 'res.users'

    is_manager = fields.Boolean(string='Encargado de tienda', help='Es encargado de tienda', defaut=False)
