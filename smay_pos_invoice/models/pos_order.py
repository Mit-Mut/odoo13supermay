# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, Warning, ValidationError
import logging, time

_logger = logging.getLogger(__name__)


class PosInvoicePosOrder(models.Model):
    _inherit = 'pos.order'

    x_metodo_pago_sat = fields.Char(string='Metodo de pago del SAT')
    x_uso_cfdi_sat = fields.Char(string='uso del cfdi')

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosInvoicePosOrder, self)._order_fields(ui_order)
        order_fields['x_metodo_pago_sat'] = ui_order['x_metodo_pago_sat']
        order_fields['x_uso_cfdi_sat'] = ui_order['x_uso_cfdi_sat']
        return order_fields

    # esta funcion se llama desde la tarea programada para el envío de las facturas cada 5 mins
    @api.model
    def _send_invoice_to_clients(self):
        invoices = self.env['account.move'].search(
            [('invoice_sent', '=', False), ('state', '=', 'open'), ('type', 'in', ['out_invoice', 'out_refund']),
             ('invoice_origin', 'not ilike', 'Factura Global')])
        for invoice in invoices:
            _logger.warning('ENVIO DE FACTURAS A CLIENTES')
            _logger.warning(str(invoice.origin))
            invoice.l10n_mx_edi_update_sat_status()
            email_act = invoice.action_invoice_sent()
            if email_act and email_act.get('context'):
                email_ctx = email_act['context']
                email_ctx.update(default_email_from=invoice.company_id.email)
                invoice.message_post_with_template(email_ctx.get('default_template_id'))
                invoice.write({
                    'sent': True
                })
            # time.sleep(1)
        if invoices:
            self.env['mail.mail'].process_email_queue()

    def _prepare_invoice_vals(self):
        invoice_fields = super(PosInvoicePosOrder, self)._prepare_invoice_vals()
        if self.x_metodo_pago_sat and self.x_uso_cfdi_sat:
            invoice_fields['l10n_mx_edi_payment_method_id'] = int(self.x_metodo_pago_sat)
            invoice_fields['l10n_mx_edi_usage'] = self.x_uso_cfdi_sat
        return invoice_fields

    def _prepare_invoice_line(self, order_line):
        invoice_line = super(PosInvoicePosOrder, self)._prepare_invoice_line(order_line)
        cuenta_analitica = self.env['pos.session'].search(
            [('state', '=', 'opened'), ('user_id', '=', self.env.user.id)]).config_id.x_cuenta_analitica
        invoice_line['analytic_account_id'] = cuenta_analitica
        return invoice_line
