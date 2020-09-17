# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, date, time, timedelta
import pytz
import logging, time

_logger = logging.getLogger(__name__)


class herenciasMOVE(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, vals):
        res = super(herenciasMOVE, self).create(vals)
        _logger.warning('CREATEEEEEEEEEEEEEE FCTURA')
        _logger.warning(str(res))
        _logger.warning(str(vals))
        return res


class herenciasMOVEline(models.Model):
    _inherit = 'account.move.line'

    '''@api.model
    def create(self, vals):
        res = super(herenciasMOVEline, self).create(vals)
        _logger.warning('CREATEEEEEEEEEEEEEE_LINEEEEEEEEEEEEE')
        _logger.warning(str(res))
        _logger.warning(str(vals))
        return res'''


class GlobalInvoiceWizard(models.TransientModel):
    _name = "global.invoice.wizard"
    _description = 'Save data for global invoice'

    start_date = fields.Datetime(string="Fecha de inicio", required=True, default=lambda self: self.get_date('START'))
    end_date = fields.Datetime(string="Fecha Final", required=True, default=lambda self: self.get_date('END'))
    company_id = fields.Many2one('res.company', 'Compañia', required=True,
                                 default=lambda self: self.get_company(), readonly=True)

    sucursal_id = fields.Char(string='Sucursal', default=lambda self: self.get_sucursal(), readonly=True)
    pay_method_id = fields.Selection([('1', 'Efectivo'),
                                      ('2', 'Cheque nominativo'),
                                      ('3', 'Transferencia electrónica de fondos'),
                                      ('4', 'Tarjeta de Crédito'),
                                      ('5', 'Monedero Electrónico'),
                                      ('6', 'Dinero Electrónico'),
                                      ('7', 'Vales de despensa'),
                                      ('8', 'Dación de pagos'),
                                      ('9', 'Pago por subrogración'),
                                      ('10', 'Pago por consignación'),
                                      ('11', 'Condonación'),
                                      ('12', 'Compensación'),
                                      ('13', 'Novacion'),
                                      ('14', 'Confusión'),
                                      ('15', 'Remisión de deuda'),
                                      ('16', 'Prescripción o caducidad'),
                                      ('17', 'A satisfacción del cliente'),
                                      ('18', 'Tarjeta de Débito'),
                                      ('19', 'Tarjeta de Servicio'),
                                      ('20', 'Aplicación de anticipos'),
                                      ('21', 'Intermediario pagos'),
                                      ('22', 'Por definir'),
                                      ], 'Metodo de pago', default='22', required=True)

    uso_cfdi_id = fields.Selection([('G01', 'Adquisición de mercancías.'),
                                    ('G02', 'Devoluciones, descuentos o bonificaciones.'),
                                    ('G03', 'Gastos en general.'),
                                    ('I01', 'Construcciones.'),
                                    ('I02', 'Mobilario y equipo de oficina por inversiones.'),
                                    ('I03', 'Equipo de transporte.'),
                                    ('I04', 'Equipo de cómputo y accesorios.'),
                                    ('I05', 'Dados, troqueles, moldes, matrices y herramental.'),
                                    ('I06', 'Comunicaciones telefónicas.'),
                                    ('I07', 'Comunicaciones satelitales.'),
                                    ('I08', 'Otra maquinaria y equipo.'),
                                    ('D01', 'Honorarios médicos, dentales y gastos hospitalarios.'),
                                    ('D02', 'Gastos médicos por incapacidad o discapacidad.'),
                                    ('D03', 'Gastos funerales.'),
                                    ('D04', 'Donativos.'),
                                    ('D05',
                                     'Intereses reales efectivamente pagados por créditos hipotecarios (casa habitación).'),
                                    ('D06', 'Aportaciones voluntarias al SAR.'),
                                    ('D07', 'Primas por seguros de gastos médicos.'),
                                    ('D08', 'Gastos de transportación escolar obligatoria.'),
                                    ('D09',
                                     'Depósitos en cuentas para el ahorro, primas que tengan como base planes de pensiones.'),
                                    ('D10', 'Pagos por servicios educativos (colegiaturas).'),
                                    ('P01', 'Por definir.'),
                                    ], 'Uso del CFDI', default='P01', required=True)

    def get_sucursal(self):
        sucursal = self.env.user.sucursal_id

        if not self.env.user.is_manager:
            raise UserError('Solo el GERENTE/CONCILIADOR puede generar la factura global.')

        if not sucursal:
            raise UserError(
                'No tiene sucursal asignada para generar la factura global. Contacta al administrador para asignar la sucursal.')

        pos_configs = []
        for pos_config in self.env.user.pos_config_ids:
            if not pos_config.es_checador_precios:
                pos_configs.append(pos_config.id)

        if not self.env.user.company_id.invoice_partner_id:
            raise UserError(
                'El Cliente de facturacion global no esta asignado en la compañia, reportalo con el administrador.')

        if not self.env.user.company_id.invoice_product_id:
            raise UserError(
                'El Producto para la facturación global no esta asignado en la compañia, reportalo con el administrador.')

        if not self.env.user.pos_config_ids:
            raise UserError('No tienes puntos de ventas asignados para la generación de la factura global')
        else:
            if len(sucursal) > 1:
                raise UserError(
                    'Tienes más de una sucursal asignada, contacta al administrador para la correcta configuración.')
            else:
                for pos_config_id in pos_configs:
                    if sucursal.id != self.env['pos.config'].browse(pos_config_id).sucursal_id.id:
                        raise UserError('No puedes generar la factura global porque el punto de venta >> ' + str(
                            self.env['pos.config'].browse(pos_config_id).name) + ' << esta asignado a la sucursal ' +
                                        self.env['pos.config'].browse(
                                            pos_config_id).sucursal_id.name + ' y tu sucursal asignada es ' + sucursal.name + '. Contacta al administrador para la correcta configuración de tu usuario.')
                return sucursal.name

    def get_date(self, label):
        default_datetime = ''

        if label == 'START':
            default_datetime = str(datetime.strptime(str(date.today()) + ' 00:00:00', "%Y-%m-%d %H:%M:%S"))
        if label == 'END':
            default_datetime = str(datetime.strptime(str(date.today()) + ' 23:59:59', "%Y-%m-%d %H:%M:%S"))

        if default_datetime != '':
            local = pytz.timezone(str(self.env.get('res.users').browse(self._uid).tz))
            fecha = datetime.strptime(default_datetime, "%Y-%m-%d %H:%M:%S")
            local_dt = local.localize(fecha, is_dst=None)
            utc_dt = local_dt.astimezone(pytz.utc)
            return str(utc_dt)[0:19]
        return '2017-02-02 17:30:00'

    def get_company(self):
        return self.env.user.company_id.id

    def generate_invoice(self):
        pos_configs = []
        user_sucursal = self.env.user.sucursal_id
        for pos_config in self.env.user.pos_config_ids:
            if not pos_config.es_checador_precios and pos_config.sucursal_id.id == user_sucursal.id:
                pos_configs.append(pos_config.id)

        # revisa que se hayan hecho las notas de credito en dias anteriores
        sessions_not_invoicing_credit_notes = self.env['pos.session'].search([('start_at', '<', self.start_date),
                                                                              ('user_id.company_id', '=',
                                                                               self.env.user.company_id.id),
                                                                              ('config_id', 'in', pos_configs),
                                                                              ('notas_credito_global', '=', False),
                                                                              ('config_id.sucursal_id.id', '=',
                                                                               user_sucursal.id)])

        _logger.warning("Faltan las notas de credito de estas sessiones" + str(sessions_not_invoicing_credit_notes))

        if sessions_not_invoicing_credit_notes:
            message = 'No se han realizado las notas de credito de las siguientes sesiones:\n'
            for session in sessions_not_invoicing_credit_notes:
                message += str(session.name) + ' - ' + str(session.start_at)[0:10] + '\n'
            raise UserError(message)

        sessions_to_invoicing = self.env['pos.session'].search([
            # ('state', '=', 'closed'),
            ('start_at', '>=', self.start_date),
            ('start_at', '<=', self.end_date),
            ('user_id.company_id', '=', self.env.user.company_id.id),
            ('config_id', 'in', pos_configs),
            ('config_id.sucursal_id.id', '=', user_sucursal.id),
            ('factura_global', '=', False),
        ])

        _logger.warning("estas sessiones seran las que se facturaran" + str(sessions_to_invoicing))

        if not sessions_to_invoicing:
            raise UserError('No existen sesiones para facturar en las fechas indicadas')

        orders = 0
        for session in sessions_to_invoicing:
            orders += len(session.order_ids)
            if len(session.order_ids) == 0:
                session.sudo(True).write({
                    'factura_global': True
                })

        if orders == 0:
            return

        _logger.warning("estas son las ordenes que se van a facturasrrrrr" + str(orders))

        # aqui verifico que no haya ordenes con cliente asignado y sin facturar
        orders_without_invoicing = []
        for session in sessions_to_invoicing:
            for order in session.order_ids:
                if order.partner_id.id != self.env.user.company_id.invoice_partner_id.id and order.state != 'invoiced' and order.amount_total > 0:
                    orders_without_invoicing.append(order.pos_reference)
        if len(orders_without_invoicing) > 0:
            message = 'Las siguientes ordenes tiene cliente asignado pero no fueron facturadas:\n'
            for ord in orders_without_invoicing:
                message += str(ord) + ',\n'

            raise UserError(message)

        orders = 0
        global_orders = 0
        for session in sessions_to_invoicing:
            for order in session.order_ids:
                if order.state != 'invoiced':
                    orders += 1
            if orders == 0:
                session.sudo(True).write({
                    'factura_global': True
                })
            global_orders += orders

        if global_orders == 0:
            return

            # raise UserWarning('No hay ordenes que facturar')

        # Creacion de la factura

        Invoice = self.env['account.move'].create(self._prepare_global_invoice(pos_configs))

        # self._prepare_global_invoice_line(Invoice, sessions_to_invoicing)
        _logger.warning('FACTURA DE VARIOS PRODUCTOS')
        _logger.warning(str(Invoice))

        # Invoice.compute_taxes()

        '''for tax_line in Invoice.tax_line_ids:
            tax_line.write({
                'account_analytic_id': self.env['pos.config'].browse(pos_configs[0]).x_cuenta_analitica.id,
            })'''

        # esta funcion valida la factura
        # Invoice.action_invoice_open()

        '''Invoice.write({
            'payment_ids': [(0, 0, {
                'amount': Invoice.amount_total,
                'journal_id': Invoice.journal_id.id,  # 11,
                'payment_date': str(date.today()),
                # 'communication': Invoice.number,
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': Invoice.partner_id.id,
                'partner_bank_id': '',
                'payment_method_id': self.env['account.payment.method'].search(
                    [('code', '=', 'manual'), ('payment_type', '=', 'inbound')]).id
            })]
        })'''

        # Invoice.invoice_validate()

        '''for payment in Invoice.payment_ids:
            payment.action_validate_invoice_payment()'''

        for session in sessions_to_invoicing:
            session.sudo().write({
                'factura_global': True,
                'global_invoice_name': Invoice.name,
            })

        # time.sleep(1)
        # Invoice.action_invoice_open()
        # time.sleep(5)
        # Invoice.l10n_mx_edi_update_sat_status()
        # time.sleep(2)
        '''email_act = Invoice.action_invoice_sent()

        if email_act and email_act.get('context'):
            email_ctx = email_act['context']
            email_ctx.update(default_email_from=Invoice.company_id.email)
            Invoice.message_post_with_template(email_ctx.get('default_template_id'))'''

        # return self.env.ref('account.account_invoices').report_action(Invoice)

        '''return {
            'name': _('Customer Invoice'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('account.move_form').id,
            'res_model': 'accpunt.move',
            'context': "{'type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'nodestroy': False,
            'target': 'current',
            'res_id': Invoice.id and Invoice.ids[0] or False,
        }'''

    def _prepare_global_invoice_line(self, invoice, sessions_to_invoicing):
        product = self.env.user.company_id.invoice_product_id
        # invoice_amount_tax = 0
        for session in sessions_to_invoicing:
            for order in session.order_ids:

                order_taxes = {}
                for orderline in order.lines:
                    for tax in orderline.tax_ids:
                        order_taxes[int(tax.amount)] = tax.id

                if order.state == 'invoiced' or order.amount_total <= 0:
                    continue

                # description = order.pos_reference

                for order_tax in order_taxes:
                    description = order.pos_reference + '_' + str(order_tax)
                    amount_total = 0
                    subtotal = 0
                    for orderline_2 in order.lines:
                        if order_taxes.get(order_tax) == orderline_2.tax_ids.id:
                            amount_total += orderline_2.price_subtotal_incl
                            subtotal += orderline_2.price_subtotal

                    if amount_total == 0:
                        continue

                    # aqui debo de guardar cada linea de factura

                    data_line = {
                        'name': '[' + product.name + ']  ' + description,
                        'product_id': product.id,
                        'invoice_id': invoice.id,
                        'price_unit': amount_total,
                        'price_subtotal': subtotal,
                        'account_id': self.env['account.account'].search(
                            [('name', '=', 'Ventas y/o servicios gravados a la tasa general')]).id,
                        'invoice_line_tax_ids': [(6, 0, [order_taxes.get(order_tax)])],
                        'quantity': 1,
                        'uom_id': product.uom_id.id,
                        'account_analytic_id': session.config_id.x_cuenta_analitica.id,
                    }
                    self.env['account.move.line'].create(data_line)

    def _prepare_global_invoice(self, config_ids):
        config_ids = self.env['pos.config'].search([('id', 'in', config_ids)])
        equipo_ventas = []
        journal_ids = []
        position_fiscal_ids = []
        sucursal_ids = []
        analytic_account_ids = []
        for config_id in config_ids:
            if not config_id.equipo_ventas:
                raise UserError('El punto de venta ' + config_id.name + ' no tiene equipo de venta configurado')
            else:
                equipo_ventas.append(config_id.equipo_ventas.id)
            if not config_id.invoice_journal_id:
                raise UserError('El punto de venta ' + config_id.name + ' no tiene diario de ventas configurado')
            else:
                journal_ids.append(config_id.invoice_journal_id.id)
            if not config_id.default_fiscal_position_id:
                raise UserError('El punto de venta ' + config_id.name + ' no tiene las posicion fiscal configurada')
            else:
                position_fiscal_ids.append(config_id.default_fiscal_position_id.id)
            if not config_id.sucursal_id:
                raise UserError('El punto de venta ' + config_id.name + ' no tiene sucursal asignada')
            else:
                sucursal_ids.append(config_id.sucursal_id.id)
            if not config_id.x_cuenta_analitica:
                raise UserError('El punto de venta ' + config_id.name + ' no tiene cuenta analitica asignada')
            else:
                analytic_account_ids.append(config_id.x_cuenta_analitica.id)
        if len(list(set(equipo_ventas))) > 1:
            raise UserError('Existe mas de un equipo de ventas en los puntos de venta a facturar')
        if len(list(set(journal_ids))) > 1:
            raise UserError('Existe mas de un diario de faturas en los puntos de venta a facturar')
        if len(list(set(position_fiscal_ids))) > 1:
            raise UserError('Existe mas de una posicion fiscal en los puntos de venta a facturar')
        if len(list(set(sucursal_ids))) > 1:
            raise UserError('Existe mas de una sucursal en los puntos de venta a facturar')
        if len(list(set(analytic_account_ids))) > 1:
            raise UserError('Existe mas de una cuenta analitica en los puntos de venta a facturar')

        '''[
                    0, '',
                    {
                        'account_id': 23,
                        'sequence': 10,
                        'name': 'IVA(16%) VENTAS',
                        'quantity': 1,
                        'price_unit': 12.48,
                        'discount': 0,
                        'debit': 0,
                        'credit': 12.48,
                        'amount_currency': 0,
                        'date_maturity': False,
                        'currency_id': False,
                        'partner_id': 273,
                        'product_uom_id': False,
                        'product_id': False,
                        'payment_id': False,
                        'tax_ids': [[6, False, []]],
                        'tax_base_amount': 77.97,
                        'tax_exigible': False,
                        'tax_repartition_line_id': 6,
                        'tag_ids': [[6, False, [938]]],
                        'analytic_account_id': False,
                        'analytic_tag_ids': [[6, False, []]],
                        'recompute_tax_line': False,
                        'display_type': False,
                        'is_rounding_line': False,
                        'exclude_from_invoice_tab': True,
                        'purchase_line_id': False,
                        'predict_from_name': False,
                        'predict_override_default_account': False,
                        'l10n_mx_edi_customs_number': False,
                        'l10n_mx_edi_qty_umt': 0
                    }
                ],'''

        data_invoice = {
            'partner_id': self.env['res.company'].browse(self.env.user.company_id.id).invoice_partner_id.id,
            'l10n_mx_edi_payment_method_id': self.pay_method_id,
            'l10n_mx_edi_usage': self.uso_cfdi_id,
            'user_id': self.env.user.id,
            'team_id': equipo_ventas[0],
            'journal_id': journal_ids[0],
            'fiscal_position_id': position_fiscal_ids[0],
            'type': 'out_invoice',
            'company_id': self.env.user.company_id.id,
            'invoice_date': str(date.today()),  # - timedelta(days=2)),
            'date_due': str(date.today()),
            'line_ids': [

                [
                    0, '',
                    {
                        'account_id': 30,
                        'sequence': 10,
                        'name': '[012388000190] UTIL POLVO 1 KG',
                        'quantity': 1,
                        'price_unit': 25,
                        'discount': 0, 'debit': 0,
                        'credit': 21.55, 'amount_currency': 0,
                        'date_maturity': False,
                        'currency_id': False,
                        'partner_id': 273,
                        'product_uom_id': 1,
                        'product_id': 8381,
                        'payment_id': False,
                        'tax_ids': [[6, False, [2]]],
                        'tax_base_amount': 0,
                        'tax_exigible': False,
                        'tax_repartition_line_id': False,
                        'tag_ids': [[6, False, []]],
                        'analytic_account_id': False,
                        'analytic_tag_ids': [[6, False, []]],
                        'recompute_tax_line': False,
                        'display_type': False,
                        'is_rounding_line': False,
                        'exclude_from_invoice_tab': False,
                        'purchase_line_id': False,
                        'predict_from_name': False,
                        'predict_override_default_account': False,
                        'l10n_mx_edi_customs_number': False,
                        'l10n_mx_edi_qty_umt': 0}
                ],
                [
                    0, '',
                    {
                        'account_id': 30,
                        'sequence': 10,
                        'name': '[012388003481] LIRIO COCO ANTIBACT EXH/3 120 GR',
                        'quantity': 1,
                        'price_unit': 46.4,
                        'discount': 0,
                        'debit': 0,
                        'credit': 40,
                        'amount_currency': 0,
                        'date_maturity': False,
                        'currency_id': False,
                        'partner_id': 273,
                        'product_uom_id': 1,
                        'product_id': 8596,
                        'payment_id': False,
                        'tax_ids': [[6, False, [2]]],
                        'tax_base_amount': 0, 'tax_exigible': False,
                        'tax_repartition_line_id': False,
                        'tag_ids': [[6, False, []]],
                        'analytic_account_id': False,
                        'analytic_tag_ids': [[6, False, []]],
                        'recompute_tax_line': False,
                        'display_type': False,
                        'is_rounding_line': False,
                        'exclude_from_invoice_tab': False,
                        'purchase_line_id': False,
                        'predict_from_name': False,
                        'predict_override_default_account': False,
                        'l10n_mx_edi_customs_number': False,
                        'l10n_mx_edi_qty_umt': 0
                    }
                ],
                [
                    0, '',
                    {
                        'account_id': 30,
                        'sequence': 10,
                        'name': '[012388003290] BOLD 3 CARIÑITOS LIQ. 800 GR',
                        'quantity': 1,
                        'price_unit': 19.05,
                        'discount': 0,
                        'debit': 0,
                        'credit': 16.42,
                        'amount_currency': 0,
                        'date_maturity': False,
                        'currency_id': False,
                        'partner_id': 273,
                        'product_uom_id': 1,
                        'product_id': 8661,
                        'payment_id': False,
                        'tax_ids': [[6, False, [2]]],
                        'tax_base_amount': 0,
                        'tax_exigible': False,
                        'tax_repartition_line_id': False,
                        'tag_ids': [[6, False, []]],
                        'analytic_account_id': False,
                        'analytic_tag_ids': [[6, False, []]],
                        'recompute_tax_line': False,
                        'display_type': False,
                        'is_rounding_line': False,
                        'exclude_from_invoice_tab': False,
                        'purchase_line_id': False,
                        'predict_from_name': False,
                        'predict_override_default_account': False,
                        'l10n_mx_edi_customs_number': False,
                        'l10n_mx_edi_qty_umt': 0}
                ]
                ],
            'ref': 'Factura Global - ' + str(self.start_date)[0:10] + ' - ' + self.env[
                'res.partner'].browse(
                sucursal_ids[0]).name,
        }

        data_invoice['line_ids'].append(self._get_info_tax('IVA(16%) VENTAS', data_invoice))
        data_invoice['line_ids'].append(self._get_info_tax('IEPS(8%) VENTAS', data_invoice))
        data_invoice['line_ids'].append(self._get_line_totals(data_invoice))

        _logger.warning('Dicccionario para crear la facrtura ' + str(data_invoice))
        return data_invoice

    def _get_line_totals(self, data_invoice):

        lineas = data_invoice['line_ids']

        totals = [
            0, '',
            {
                'account_id': self.env['res.company'].browse(
                    self.env.user.company_id.id).invoice_partner_id.property_account_receivable_id.id,
                'sequence': 10,
                'name': False,
                'quantity': 1,
                'price_unit': -90.45,
                #'price_unit': -0,
                'discount': 0,
                'debit': 90.45,
                #'debit': 0,
                'credit': 0,
                'amount_currency': 0,
                # 'date_maturity': '2020-09-17',
                'date_maturity': str(date.today()),
                'currency_id': False,
                # 'partner_id': 273,
                'partner_id': self.env['res.company'].browse(self.env.user.company_id.id).invoice_partner_id.id,
                'product_uom_id': False,
                'product_id': False,
                'payment_id': False,
                'tax_ids': [[6, False, []]],
                'tax_base_amount': 0,
                'tax_exigible': True,
                'tax_repartition_line_id': False,
                'tag_ids': [[6, False, []]],
                'analytic_account_id': False,
                'analytic_tag_ids': [[6, False, []]],
                'recompute_tax_line': False,
                'display_type': False,
                'is_rounding_line': False,
                'exclude_from_invoice_tab': True,
                'purchase_line_id': False,
                'predict_from_name': False,
                'predict_override_default_account': False,
                'l10n_mx_edi_customs_number': False,
                'l10n_mx_edi_qty_umt': 0
            }
        ]
        return totals
        #return lineas.append(totals)

    def _get_info_tax(self, etiqueta_impuesto, data_invoice):
        lineas = data_invoice['line_ids']
        impuesto_def = self.env['account.tax'].search([('name', '=', etiqueta_impuesto)])
        repartition_id = 0
        for imp in impuesto_def.invoice_repartition_line_ids:
            if imp.repartition_type=='tax':
                repartition_id = imp.id


        if impuesto_def:
            impuesto = [
                0, '',
                {
                    'account_id': impuesto_def.cash_basis_transition_account_id.id,
                    'sequence': 10,
                    'name': impuesto_def.name,
                    'quantity': 1,
                    'price_unit': 12.48,
                    #'price_unit': 0,
                    'discount': 0,
                    'debit': 0,
                    'credit': 12.48,
                    #'credit': 0,
                    'amount_currency': 0,
                    'date_maturity': False,
                    'currency_id': False,
                    'partner_id': self.env['res.company'].browse(self.env.user.company_id.id).invoice_partner_id.id,
                    'product_uom_id': False,
                    'product_id': False,
                    'payment_id': False,
                    'tax_ids': [[6, False, []]],
                    'tax_base_amount': 77.97,
                    #'tax_base_amount': 0,
                    'tax_exigible': False,
                    #'tax_repartition_line_id': 6,
                    #'tax_repartition_line_id': max(impuesto_def.invoice_repartition_line_ids).id,
                    'tax_repartition_line_id':repartition_id,
                    # 'tag_ids': [[6, False, [938]]],
                    'analytic_account_id': False,
                    'analytic_tag_ids': [[6, False, []]],
                    'recompute_tax_line': False,
                    'display_type': False,
                    'is_rounding_line': False,
                    'exclude_from_invoice_tab': True,
                    'purchase_line_id': False,
                    'predict_from_name': False,
                    'predict_override_default_account': False,
                    'l10n_mx_edi_customs_number': False,
                    'l10n_mx_edi_qty_umt': 0,
                }]

        #_logger.warning('SE AGREGO EL IMPUESTO' + str(lineas.append(impuesto)))

        return impuesto


class GlobalInvoiceCreditNoteWizard(models.TransientModel):
    _name = "global.invoice.credit.notes.wizard"
    _description = 'Save data for global the credit notes'

    start_date = fields.Datetime(string="Fecha de inicio", required=True, default=lambda self: self.get_date('START'))
    end_date = fields.Datetime(string="Fecha Final", required=True, default=lambda self: self.get_date('END'))
    company_id = fields.Many2one('res.company', 'Compañia', required=True, default=lambda self: self.get_company(),
                                 readonly=True)

    sucursal_id = fields.Char(string='Sucursal', default=lambda self: self.get_sucursal(), readonly=True)

    pay_method_id = fields.Selection([('1', 'Efectivo'),
                                      ('2', 'Cheque nominativo'),
                                      ('3', 'Transferencia electrónica de fondos'),
                                      ('4', 'Tarjeta de Crédito'),
                                      ('5', 'Monedero Electrónico'),
                                      ('6', 'Dinero Electrónico'),
                                      ('7', 'Vales de despensa'),
                                      ('8', 'Dación de pagos'),
                                      ('9', 'Pago por subrogración'),
                                      ('10', 'Pago por consignación'),
                                      ('11', 'Condonación'),
                                      ('12', 'Compensación'),
                                      ('13', 'Novacion'),
                                      ('14', 'Confusión'),
                                      ('15', 'Remisión de deuda'),
                                      ('16', 'Prescripción o caducidad'),
                                      ('17', 'A satisfacción del cliente'),
                                      ('18', 'Tarjeta de Débito'),
                                      ('19', 'Tarjeta de Servicio'),
                                      ('20', 'Aplicación de anticipos'),
                                      ('21', 'Intermediario pagos'),
                                      ('22', 'Por definir'),
                                      ], 'Metodo de pago', default='22', required=True, readonly=True)

    uso_cfdi_id = fields.Selection([('G01', 'Adquisición de mercancías.'),
                                    ('G02', 'Devoluciones, descuentos o bonificaciones.'),
                                    ('G03', 'Gastos en general.'),
                                    ('I01', 'Construcciones.'),
                                    ('I02', 'Mobilario y equipo de oficina por inversiones.'),
                                    ('I03', 'Equipo de transporte.'),
                                    ('I04', 'Equipo de cómputo y accesorios.'),
                                    ('I05', 'Dados, troqueles, moldes, matrices y herramental.'),
                                    ('I06', 'Comunicaciones telefónicas.'),
                                    ('I07', 'Comunicaciones satelitales.'),
                                    ('I08', 'Otra maquinaria y equipo.'),
                                    ('D01', 'Honorarios médicos, dentales y gastos hospitalarios.'),
                                    ('D02', 'Gastos médicos por incapacidad o discapacidad.'),
                                    ('D03', 'Gastos funerales.'),
                                    ('D04', 'Donativos.'),
                                    ('D05',
                                     'Intereses reales efectivamente pagados por créditos hipotecarios (casa habitación).'),
                                    ('D06', 'Aportaciones voluntarias al SAR.'),
                                    ('D07', 'Primas por seguros de gastos médicos.'),
                                    ('D08', 'Gastos de transportación escolar obligatoria.'),
                                    ('D09',
                                     'Depósitos en cuentas para el ahorro, primas que tengan como base planes de pensiones.'),
                                    ('D10', 'Pagos por servicios educativos (colegiaturas).'),
                                    ('P01', 'Por definir.'),
                                    ], 'Uso del CFDI', default='P01', required=True, readonly=True)

    def get_sucursal(self):
        sucursal = self.env.user.sucursal_id
        if not self.env.user.is_manager:
            raise UserError('Solo el GERENTE/CONCILIADOR puede generar la factura global.')

        if not sucursal:
            raise UserError(
                'No tiene sucursal asignada para generar la factura global. Contacta al administrador para asignar la sucursal.')

        pos_configs = []
        for pos_config in self.env.user.pos_config_ids:
            if not pos_config.es_checador_precios:
                pos_configs.append(pos_config.id)

        if not self.env.user.company_id.invoice_partner_id:
            raise UserError(
                'El Cliente de facturacion global no esta asignado en la compañia, reportalo con el administrador.')

        if not self.env.user.company_id.invoice_product_id:
            raise UserError(
                'El Producto para la facturación global no esta asignado en la compañia, reportalo con el administrador.')

        if not self.env.user.pos_config_ids:
            raise UserError('No tienes puntos de ventas asignados para la generación de la factura global')
        else:
            if len(sucursal) > 1:
                raise UserError(
                    'Tienes más de una sucursal asignada, contacta al administrador para la correcta configuración.')
            else:
                for pos_config_id in pos_configs:
                    if sucursal.id != self.env['pos.config'].browse(pos_config_id).sucursal_id.id:
                        raise UserError('No puedes generar la factura global porque el punto de venta >> ' + str(
                            self.env['pos.config'].browse(pos_config_id).name) + ' << esta asignado a la sucursal ' +
                                        self.env['pos.config'].browse(
                                            pos_config_id).sucursal_id.name + ' y tu sucursal asignada es ' + sucursal.name + '. Contacta al administrador para la correcta configuración de tu usuario.')
                return sucursal.name

    def generate_invoice(self):
        pos_configs = []
        user_sucursal = self.env.user.sucursal_id
        for pos_config in self.env.user.pos_config_ids:
            if not pos_config.es_checador_precios and pos_config.sucursal_id.id == user_sucursal.id:
                pos_configs.append(pos_config.id)

        self.validate_user(pos_configs)

        sessions_not_invoicing_credit_notes = self.env['pos.session'].search(
            [('start_at', '<', self.start_date),
             ('user_id.company_id', '=', self.env.user.company_id.id),
             ('config_id', 'in', pos_configs),
             ('notas_credito_global', '=', False),
             ('config_id.sucursal_id.id', '=', user_sucursal.id)])

        if sessions_not_invoicing_credit_notes:
            message = 'No se han realizado las notas de credito de las siguientes sesiones:\n'
            for session in sessions_not_invoicing_credit_notes:
                message += str(session.name) + ' - ' + str(session.start_at)[0:10] + '\n'
            raise UserError(message)

        sessions_without_invoice = self.env['pos.session'].search(
            [  # ('state', '=', 'closed'),
                ('start_at', '>=', self.start_date),
                ('start_at', '<=', self.end_date),
                ('user_id.company_id', '=', self.env.user.company_id.id),
                ('config_id', 'in', pos_configs),
                ('config_id.sucursal_id.id', '=', user_sucursal.id),
                ('notas_credito_global', '=', False),
                ('factura_global', '=', False)
            ])

        if sessions_without_invoice:
            raise UserError('Es necesario que primero realices la Facturación Global.')

        sessions_to_invoicing = self.env['pos.session'].search(
            [  # ('state', '=', 'closed'),
                ('start_at', '>=', self.start_date),
                ('start_at', '<=', self.end_date),
                ('user_id.company_id', '=', self.env.user.company_id.id),
                ('config_id', 'in', pos_configs),
                ('config_id.sucursal_id.id', '=', user_sucursal.id),
                ('notas_credito_global', '=', False),
            ])

        if not sessions_to_invoicing:
            raise UserError('No existen sesiones para generar notas de credito en las fechas indicadas')

        orders = 0
        for session in sessions_to_invoicing:
            refund_orders_without_cr = self.env['pos.order'].search(
                [('session_id', '=', session.id),
                 ('amount_total', '<', 0),
                 ('state', '!=', 'invoiced')])
            orders += len(refund_orders_without_cr)
            if len(refund_orders_without_cr) == 0:
                session.sudo().write({
                    'notas_credito_global': True
                })

        if orders == 0:
            return

        pos_references = []
        for session in sessions_to_invoicing:
            refund_orders_without_cr = self.env['pos.order'].search(
                [('session_id', '=', session.id),
                 ('amount_total', '<', 0),
                 ('state', '!=', 'invoiced')])
            for refund_order in refund_orders_without_cr:
                pos_references.append(refund_order.pos_reference)

        list_invoices = []

        for session in sessions_to_invoicing:
            refund_orders_without_cr = self.env['pos.order'].search(
                [('session_id', '=', session.id),
                 ('amount_total', '<', 0),
                 ('state', '!=', 'invoiced')])
            for refund_order in refund_orders_without_cr:
                invoice_line_ids = self.env['account.move.line'].search(
                    [('name', 'like', refund_order.pos_reference),
                     ('invoice_id.type', '=', 'out_invoice'),
                     ('invoice_id', '>', 140),
                     ('invoice_id.state', '!=', 'draft')])
                if not invoice_line_ids:
                    continue

                invoice_line_id = []
                for line in invoice_line_ids:
                    invoice_line_id.append(line.id)

                invoice = self.env['account.move'].search(
                    [('invoice_line_ids', 'in', invoice_line_id)])
                invoice.l10n_mx_edi_update_sat_status()

                refund_invoice = self.env['account.move'].search(
                    [('origin', 'like', invoice.origin),
                     ('type', '=', 'out_refund'),
                     ('id', '>', 140),
                     ('state', '=', 'draft')])

                if not refund_invoice:
                    refund_invoice = invoice.refund()
                    refund_invoice.write({
                        'journal_id': invoice.journal_id.id,
                        'origin': invoice.origin
                    })
                    for line in refund_invoice.invoice_line_ids:
                        line.unlink()

                order_taxes = {}
                for line in refund_order.lines:
                    for tax in line.tax_ids:
                        order_taxes[int(tax.amount)] = tax.id

                for order_tax in order_taxes:
                    description = refund_order.pos_reference + '_' + str(order_tax)
                    amount_total = 0
                    subtotal = 0
                    for orderline_2 in refund_order.lines:
                        if order_taxes.get(order_tax) == orderline_2.tax_ids.id:
                            amount_total += abs(orderline_2.price_subtotal_incl)
                            subtotal += abs(orderline_2.price_subtotal)

                    if amount_total == 0:
                        continue

                    product = self.env.user.company_id.invoice_product_id

                    data_line = {
                        'name': '[' + product.name + ']  ' + description,
                        'product_id': product.id,
                        'invoice_id': refund_invoice.id,
                        'price_unit': amount_total,
                        'price_subtotal': subtotal,
                        'account_id': self.env['account.account'].search(
                            [('name', '=', 'Ventas y/o servicios gravados a la tasa general')]).id,
                        'invoice_line_tax_ids': [(6, 0, [order_taxes.get(order_tax)])],
                        'quantity': 1,
                        'uom_id': product.uom_id.id,
                        'account_analytic_id': session.config_id.x_cuenta_analitica.id,
                    }
                    self.env['account.move.line'].sudo().create(data_line)

                refund_invoice.compute_taxes()

                for tax_line in refund_invoice.tax_line_ids:
                    tax_line.write({
                        'account_analytic_id': self.env['pos.config'].browse(pos_configs[0]).x_cuenta_analitica.id,
                    })
                list_invoices.append(refund_invoice.id)
        for session in sessions_to_invoicing:
            session.write({
                'notas_credito_global': True
            })

        invoices = list(set(list_invoices))

        if len(invoices) > 0:
            refund_invoices = self.env['account.move'].search([('id', 'in', invoices)])
            for inv in refund_invoices:
                inv.action_invoice_open()

            # time.sleep(3)
            for invoice_id in invoices:
                inv = self.env['account.move'].browse(invoice_id)
                # inv.action_invoice_sent()
                inv.write({
                    'origin': inv.origin + ' Devoluciones ' + str(self.start_date)[0:10]
                })
            return self.env.ref('account.account_invoices').report_action(refund_invoices)
        return

    def validate_user(self, config_ids):
        config_ids = self.env['pos.config'].search([('id', 'in', config_ids)])
        equipo_ventas = []
        journal_ids = []
        position_fiscal_ids = []
        sucursal_ids = []
        analytic_account_ids = []
        for config_id in config_ids:
            if not config_id.equipo_ventas:
                raise UserError('El punto de venta ' + config_id.name + ' no tiene equipo de venta configurado')
            else:
                equipo_ventas.append(config_id.equipo_ventas.id)

            if not config_id.invoice_journal_id:
                raise UserError('El punto de venta ' + config_id.name + ' no tiene diario de ventas configurado')
            else:
                journal_ids.append(config_id.invoice_journal_id.id)

            if not config_id.default_fiscal_position_id:
                raise UserError('El punto de venta ' + config_id.name + ' no tiene las posicion fiscal configurada')
            else:
                position_fiscal_ids.append(config_id.default_fiscal_position_id.id)

            if not config_id.sucursal_id:
                raise UserError('El punto de venta ' + config_id.name + ' no tiene sucursal asignada')
            else:
                sucursal_ids.append(config_id.sucursal_id.id)

            if not config_id.x_cuenta_analitica:
                raise UserError('El punto de venta ' + config_id.name + ' no tiene cuenta analitica asignada')
            else:
                analytic_account_ids.append(config_id.x_cuenta_analitica.id)

        if len(list(set(equipo_ventas))) > 1:
            raise UserError('Existe mas de un equipo de ventas en los puntos de venta a facturar')

        if len(list(set(journal_ids))) > 1:
            raise UserError('Existe mas de un diario de faturas en los puntos de venta a facturar')

        if len(list(set(position_fiscal_ids))) > 1:
            raise UserError('Existe mas de una posicion fiscal en los puntos de venta a facturar')

        if len(list(set(sucursal_ids))) > 1:
            raise UserError('Existe mas de una sucursal en los puntos de venta a facturar')

        if len(list(set(analytic_account_ids))) > 1:
            raise UserError('Existe mas de una cuenta analitica en los puntos de venta a facturar')

        ###

    def get_date(self, label):

        default_datetime = ''
        _logger.warning('TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT')

        if label == 'START':
            default_datetime = str(datetime.strptime(str(date.today()) + ' 00:00:00', "%Y-%m-%d %H:%M:%S"))
        if label == 'END':
            default_datetime = str(datetime.strptime(str(date.today()) + ' 23:59:59', "%Y-%m-%d %H:%M:%S"))

        _logger.warning('GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG' + default_datetime)

        if default_datetime != '':
            local = pytz.timezone(str(self.env.get('res.users').browse(self._uid).tz))
            fecha = datetime.strptime(default_datetime, "%Y-%m-%d %H:%M:%S")
            local_dt = local.localize(fecha, is_dst=None)
            utc_dt = local_dt.astimezone(pytz.utc)
            return str(utc_dt)
        return '2017-02-02 17:30:00'

    def get_company(self):
        return self.env.user.company_id.id
