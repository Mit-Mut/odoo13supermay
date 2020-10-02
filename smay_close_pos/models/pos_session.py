# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging, time

_logger = logging.getLogger(__name__)


class PosSessionSmayCloseSession(models.Model):
    _inherit = 'pos.session'

    @api.model
    def get_session_start_at(self, session_id):
        return self.browse(session_id).start_at

    @api.model
    def get_unsigned_invoices(self, session_id):
        session = self.browse(session_id)
        unsigned_orders = {}
        for orders in session.order_ids:
            for order in orders:
                if order.account_move.l10n_mx_edi_pac_status == 'retry' or order.account_move.l10n_mx_edi_pac_status == 'to_sign' and order.partner_id.id != self.env.user.company_id.invoice_partner_id.id:
                    unsigned_orders[order.pos_reference] = order.account_move.name
        return unsigned_orders

    @api.model
    def action_pos_session_closing_control_from_pos(self, session_id):
        session = self.env['pos.session'].browse(session_id)
        for order in session.order_ids:
            if order.partner_id.id != self.env.user.company_id.invoice_partner_id.id and order.state != 'invoiced' and order.amount_total > 0:
                return -2
        if abs(session.cash_register_total_entry_encoding) > session.config_id.amount_authorized_diff:
            return -1
        '''if self.user_has_groups('point_of_sale.group_pos_user'):
            time.sleep(10)
            return 0'''
        session.action_pos_session_closing_control()
        return True

    @api.model
    def get_cash_register_total_entry_encoding(self, id_session):
        return self.env['pos.session'].browse(id_session).cash_register_total_entry_encoding

    @api.model
    def get_session_state(self, session_id):
        return self.browse(session_id).state


class AccountBankStmtSmayCloseSession(models.Model):
    _inherit = 'account.bank.statement.cashbox'

    @api.model
    def return_session_fund(self, session_id, cashbox_lines_ids):
        session = self.env['pos.session'].browse(session_id)
        for statement in session.statement_ids:

            if statement.cashbox_start_id.id > 0 and statement.cashbox_end_id.id == False:
                cashbox_out = self.env['account.bank.statement.cashbox'].create({})
                for cashbox_lines_id in cashbox_lines_ids:
                    cashbox_out.write({
                        'cashbox_lines_ids': [
                            (
                                0, 0, {
                                    'coin_value': cashbox_lines_id.get('coin_value'),
                                    'number': cashbox_lines_id.get('number'),
                                }
                            )
                        ]
                    })
                total_fund = 0
                for line in cashbox_out.cashbox_lines_ids:
                    total_fund = total_fund + (line.coin_value * line.number)
                statement.write({
                    'cashbox_end_id': cashbox_out.id,
                    'balance_end_real': total_fund,
                })
        return True
