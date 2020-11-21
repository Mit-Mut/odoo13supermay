# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
# 
#################################################################################
from odoo import fields, models

'''
FECHA:		20201120 
VERSIÓN:	v13.0.0.1:
DESCRIPCIÓN:
		En la configuración del punto de venta añade los siguientes campos para poner restriccciones de venta y visualización
		
CAMPOS:
    
    wk_display_stock : Bandera para mostrar o no el stock en el POS.
    wk_stock_type: Cantidad presentada en el POS
    wk_deny_val: Bandera para no dejar vender el producto sin stock
    wk_error_msg : Mensaje que sera presentado en el POS al negar la venta.
    wk_hide_out_of_stock: bandera para ocultar productos sin stock    
'''


class PosConfig(models.Model):
    _inherit = 'pos.config'

    wk_display_stock = fields.Boolean('Display stock in POS', default=True)
    wk_stock_type = fields.Selection(
        [('available_qty', 'Available Quantity(On hand)'), ('forecasted_qty', 'Forecasted Quantity'),
         ('virtual_qty', 'Quantity on Hand - Outgoing Qty')], string='Stock Type', default='available_qty')
    wk_continous_sale = fields.Boolean('Allow Order When Out-of-Stock')
    wk_deny_val = fields.Integer('Deny order when product stock is lower than ')
    wk_error_msg = fields.Char(string='Custom message', default="Product out of stock")
    wk_hide_out_of_stock = fields.Boolean(string="Hide Out of Stock products", default=True)
