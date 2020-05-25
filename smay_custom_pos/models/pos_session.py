# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)


class SmayCustomPosSession(models.Model):
    _inherit = 'pos.session'
    total_fund = fields.Float(compute='_get_real_fund')

    @api.depends('cash_register_balance_start', 'cash_register_balance_end_real')
    def _get_real_fund(self):
        self.total_fund = self.cash_register_balance_start - self.cash_register_balance_end_real

    '''@api.model
    def action_pos_session_open(self):
        for session in self.filtered(lambda session: session.state == 'opening_control'):
            if session.config_id.fondo_caja != session.cash_register_balance_start:  # and statement.cashbox_start_id:
                raise ValidationError("Falta asignar : $ " + str(session.config_id.fondo_caja) + " del Fondo de Caja.")
            for statement in session.statement_ids:
                if not statement.cashbox_start_id and statement.journal_id.type == 'cash':
                    raise ValidationError("Confirma el Fondo de Caja.")
        return super(SmayCustomPosSession, self).action_pos_session_open()'''


    '''
    def action_pos_session_closing_control(self):
        for session in self:
            for statement in session.statement_ids:
                if statement.balance_end_real != statement.balance_start and statement.cashbox_start_id:
                    raise ValidationError(
                        "Debes dejar  : $" + str(session.config_id.fondo_caja) + " del Fondo de Caja.")
            super(SmayCustomPosSession, self).action_pos_session_closing_control()
            session.action_pos_session_close()'''

    '''@api.model
    def action_pos_session_close(self):
        for session in self:
            for st in session.statement_ids:
                raise UserError(str(st.difference)+'  '+str(session.config_id.amount_authorized_diff))
                if abs(st.difference) > session.config_id.amount_authorized_diff:
                    if not self.user_has_groups('point_of_sale.group_pos_manager'):
                        # raise UserError(_("Your ending balance is too different from the theoretical cash closing (%.2f), the maximum allowed is: %.2f. You can contact your manager to force it.") % (st.difference, st.journal_id.amount_authorized_diff))
                        # _logger.warning('No es managaer')
                        raise UserError(
                            "La diferencia de efectivo es mayor a lo permitido : %.2f. . Contacta al encargado para forzar el cierre." % (
                                session.config_id.amount_authorized_diff))

            return super(SmayCustomPosSession, self).action_pos_session_close()'''
