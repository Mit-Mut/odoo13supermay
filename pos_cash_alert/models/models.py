# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
# 
#################################################################################

from odoo import api, fields, models
from odoo.exceptions import UserError, Warning, ValidationError
import logging

_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = 'pos.config'

    # cash_threshold = fields.Float('Monto Maximo en caja', default=0, help='Monto maximo permitido en caja.')
    cash_withdraw = fields.Float('Monto por retiro', default=0,
                                 help="La alarma en el punto de venta se lanza al llegar a este monto de venta.")


class PosRetirements(models.Model):
    _name = 'pos.retirement.denominations'
    _description = 'This model saves the information of bill denominations of retirements'

    # statement_line_id = fields.Many2one('account.bank.statement.line', 'Retiros')
    cashbox_out_id = fields.Integer(default=0)
    valor_moneda = fields.Float(default=0)
    cantidad_moneda = fields.Float(default=0)
    x_statement_ids = fields.Many2one('account.bank.statement.line', 'retiro')


class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.model
    def get_unsigned_invoices(self, session_id):
        session = self.browse(session_id)
        unsigned_orders = {}
        for orders in session.order_ids:
            for order in orders:
                if order.account_move:
                    #if (order.account_move.l10n_mx_edi_pac_status == 'retry' or order.account_move.l10n_mx_edi_pac_status == 'to_sign'):
                    _logger.warning('VALOR DEL TIMBRE'+str(order.account_move.l10n_mx_edi_pac_status))
                     _logger.warning('factura'+str(order.account_move.id))
                    if order.account_move.l10n_mx_edi_pac_status != 'signed':
                        unsigned_orders[order.pos_reference] = order.account_move.name
        return unsigned_orders

    def get_cash_register_difference(self):
        return self.cash_register_id.difference

    def get_cash_register_balance_start(self):
        return self.cash_register_balance_start

    def get_cash_register_total_entry_encoding(self):
        return self.cash_register_total_entry_encoding

    def set_cash_box_out_value(self, kwargs):
        if kwargs['check_cash'] and kwargs['amount'] > self.cash_register_total_entry_encoding:
            return -1

        bank_statements = [record.cash_register_id for record in self if record.cash_register_id]
        values = {}
        for record in bank_statements:
            if not record.journal_id:
                # raise UserError(_("Please check that the field 'Journal' is set on the Bank Statement"))
                return {
                    'msg': "Please check that the field 'Journal' is set on the Bank Statement",
                    'status': False
                }
            if not record.journal_id.company_id.transfer_account_id:
                # raise UserError(_("Please check that the field 'Transfer Account' is set on the company."))
                return {
                    'msg': "Please check that the field 'Transfer Account' is set on the company.",
                    'status': False
                }
            amount = kwargs['amount']

            last_id_out = 0;
            last_id_out_r = self.get_last_cash_box_out_id("sequence_cashbox_out_id", record.journal_id.id,
                                                          record.journal_id.company_id.id,
                                                          kwargs['sucursal_id'])  # ,kwargs['reason'])
            if last_id_out_r:
                last_id_out = last_id_out_r

            values = {
                'date': record.date,
                'statement_id': record.id,
                'journal_id': record.journal_id.id,
                'amount': -amount if amount > 0.0 else amount,
                'account_id': record.journal_id.company_id.transfer_account_id.id,
                'ref': kwargs['ref'],
                'name': kwargs['reason'],
                'comment': kwargs['comment'],
                'x_sucursal_id': kwargs['sucursal_id'],
                'sequence_cashbox_out_id': last_id_out + 1,
            }
            record.write({'line_ids': [(0, False, values)]})

            for denomination in kwargs['denominations'].keys():
                self.env['pos.retirement.denominations'].sudo().create({
                    'cantidad_moneda': kwargs['denominations'][denomination],
                    'valor_moneda': denomination,
                    'cashbox_out_id': last_id_out + 1,
                    'x_statement_ids': record.line_ids[0].id
                })
        return str(last_id_out + 1).zfill(6)
        # return {
        #				'msg':"Cash withdraw",
        #					'status':True
        # }

    @api.model
    def get_last_cash_box_out_id(self, name, journal_id, company_id, sucursal_id):  # ,razon):
        try:
            result = {}
            sql_query = ""
            sql_query = 'SELECT sequence_cashbox_out_id as scid FROM account_bank_statement_line WHERE'
            sql_query += ' journal_id = %s'
            sql_query += ' AND company_id = %s'
            sql_query += ' AND x_sucursal_id = %s'
            # sql_query += ' AND name = %s'
            sql_query += ' ORDER BY scid DESC LIMIT 1'
            params = (journal_id, company_id, sucursal_id)  # , razon)
            result = self.env.cr.execute(sql_query, params)
            response = self.env.cr.fetchone()

            if response:
                return response[0]
            return 0

        except UserError:
            return "internal error"


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    sequence_cashbox_out_id = fields.Integer(index=True, help="Gives the sequence cashbox out", default=0)
    comment = fields.Char()
    x_sucursal_id = fields.Many2one('res.partner', 'Sucursal')
    # denomination_ids = fields.One2many('pos.retirement.denominations', 'sequence_cashbox_out_id', 'Denominacion')
