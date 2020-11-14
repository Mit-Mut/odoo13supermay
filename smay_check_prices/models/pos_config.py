# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SmayCheckPricesPosConfig(models.Model):
    _inherit = 'pos.config'

    es_checador_precios = fields.Boolean(string="Verificador de precios ", default=False,
                                         help="Se configura para que haga la funcion de verificador de precios para el cliente.")

    mostrar_existencias = fields.Boolean(string='Muestra las existencia en el checador', default=False,
                                         help='Se muestran las existencias en la ventana de los precios en el checador')
