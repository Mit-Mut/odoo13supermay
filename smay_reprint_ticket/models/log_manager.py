# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
from datetime import datetime, date, time, timedelta

_logger = logging.getLogger(__name__)


class SmayReprintTicketLogManager(models.Model):
    _name = 'log.manager'
    _description = 'Guarda las acciones realizadas por el encargado de tienda'

    sucursal_id = fields.Many2one('res.partner', string='Sucursal de la operacion')
    cajero_id = fields.Many2one('res.users', string='Cajero que realiza la operacion')
    manager_id = fields.Many2one('res.users', string='Encargado que valida la operacion')
    operacion = fields.Char(string='Operacion Realizada')
