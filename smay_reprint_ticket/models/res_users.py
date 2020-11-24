# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
from datetime import datetime, date, time, timedelta

_logger = logging.getLogger(__name__)


class SmayReprintTicketResUser(models.Model):
    _inherit = 'res.users'

    
    
    #is_manager = fields.Boolean(string='Es encargado', default=False)
    pos_security_pin = fields.Char(string='PIN para punto de venta')

    _sql_constraints = [
        ('pos_security_pin_uniq', 'unique(pos_security_pin)',
         "El PIN ingresado ya esta siendo utilizado por otro usuario.")]
