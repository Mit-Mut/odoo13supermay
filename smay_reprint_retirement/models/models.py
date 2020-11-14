# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, date, time, timedelta
import logging

_logger = logging.getLogger(__name__)


class smay_reprint_retirement(models.Model):
    _inherit = 'pos.config'

    @api.model
    def get_data_retirement(self, folio, sucursal_id, pos_config_id):
        today = datetime.now().replace(microsecond=0)
        allowed_date = today - timedelta(days=self.env['pos.config'].browse(pos_config_id).days_of_reprint)
        retirement = self.env['account.bank.statement.line'].search(
            [('create_date', '<=', allowed_date), ('sequence_cashbox_out_id', '=', folio),
             ('x_sucursal_id', '=', sucursal_id)])

        # retiro fuera de rango de reimpresion
        if retirement:
            return 0

        respuesta = {}
        retirement = self.env['account.bank.statement.line'].search(
            [('sequence_cashbox_out_id', '=', folio), ('x_sucursal_id', '=', sucursal_id)])
        if retirement:
            respuesta['cashier'] = retirement.create_uid.name
            respuesta['moneyOut'] = '$ ' + '{:,.2f}'.format(abs(retirement.amount))
            respuesta['reason'] = retirement.name.upper()
            respuesta['comment'] = retirement.comment
            respuesta['last_id_out'] = retirement.sequence_cashbox_out_id
            respuesta['date_retirement'] = retirement.create_date

            denominations = self.env['pos.retirement.denominations'].search([('x_statement_ids', '=', retirement.id)])
            _denominations = []
            _denom = {}
            for denom in denominations:
                _denom['denomination'] = '$ ' + '{:,.2f}'.format(denom.valor_moneda)
                _denom['qty'] = '{:,.2f}'.format(denom.cantidad_moneda)
                _denom['amount'] = '$ ' + '{:,.2f}'.format(denom.valor_moneda * denom.cantidad_moneda)
                _denominations.append(_denom)
                _denom = {}
            respuesta['denominations'] = _denominations
        else:
            return -1
        return respuesta
