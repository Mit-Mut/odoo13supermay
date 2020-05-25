# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)


class SmayCustomPosResUser(models.Model):
    _inherit = 'res.users'

    sucursal_id = fields.Many2one('res.partner', string='Sucursal asignada al usuario')
