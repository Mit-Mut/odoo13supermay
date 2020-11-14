# -*- coding: utf-8 -*-


from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class GlobalInvoiceResCompany(models.Model):
    _inherit = 'res.company'

    invoice_partner_id = fields.Many2one('res.partner', string='Cliente factura global')
    invoice_product_id = fields.Many2one('product.product', string='Producto para la factura global')


class GlobalInvoiceResUser(models.Model):
    _inherit = 'res.users'

    sucursal_id = fields.Many2one('res.partner', string='Sucursal asignada al usuario')


class GlobalInvoicePosOrder(models.Model):
    _inherit = 'pos.order'

    sucursal_id = fields.Many2one('res.partner', string='Sucursal')

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(GlobalInvoicePosOrder, self)._order_fields(ui_order)
        order_fields['sucursal_id'] = self.env['pos.session'].search(
            [('user_id', '=', self.env.user.id),
             ('state', '=', 'opened')]).config_id.sucursal_id.id  # self.env.user.sucursal_id.id
        if not order_fields['partner_id']:
            order_fields['partner_id'] = self.env.user.company_id.invoice_partner_id.id
        return order_fields

    def _prepare_invoice(self):
        invoice_fields = super(GlobalInvoicePosOrder, self)._prepare_invoice()
        invoice_fields['team_id'] = self.env['pos.session'].search(
            [('user_id', '=', self.env.user.id), ('state', '=', 'opened')]).config_id.equipo_ventas.id
        return invoice_fields


class GlobalInvoicePosSesion(models.Model):
    _inherit = 'pos.session'

    factura_global = fields.Boolean(string='Factura Global', default=False)
    global_invoice_name = fields.Char(string='Nombre de Factura', default='')

    notas_credito_global = fields.Boolean(string='Global Notas de Credito ', default=False)


class GlobalInvoicePosConfig(models.Model):
    _inherit = 'pos.config'

    equipo_ventas = fields.Many2one('crm.team', string='Equipo de venta')


class GlobalInvoiceAccountPayment(models.Model):
    _inherit = 'account.payment'

    def l10n_mx_edi_is_required(self):
        # raise UserWarning(str(self.invoice_ids.l10n_mx_edi_cfdi_uuid))
        # super(GlobalInvoiceAccountPayment, self).l10n_mx_edi_is_required()
        if self.invoice_ids.partner_id.id == self.env.user.company_id.invoice_partner_id.id:
            return False
        return super(GlobalInvoiceAccountPayment, self).l10n_mx_edi_is_required()
