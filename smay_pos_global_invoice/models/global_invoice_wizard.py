# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, date, time, timedelta
import pytz
import logging, time

_logger = logging.getLogger(__name__)


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
                                      ], 'Metodo de pago', default='1', required=True)

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
                                    ], 'Uso del CFDI', default='G01', required=True)

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
        sessions_not_invoicing_credit_notes = self.env['pos.session'].search([('start_at', '<=', self.start_date),
                                                                              ('user_id.company_id', '=',
                                                                               self.env.user.company_id.id),
                                                                              ('config_id', 'in', pos_configs),
                                                                              ('notas_credito_global', '=', False),
                                                                              ('config_id.sucursal_id.id', '=',
                                                                               user_sucursal.id)])

        if sessions_not_invoicing_credit_notes:
            message = 'No se han realizado las notas de credito de las siguientes sesiones:\n'
            for session in sessions_not_invoicing_credit_notes:
                message += str(session.name) + ' - ' + str(session.start_at)[0:10] + '\n'
            raise UserError(message)

        # revisa que haya sessines sin haber generado la factura global y que ya esten cerradas
        sessions_to_invoicing = self.env['pos.session'].search([
            ('state', '=', 'closed'),
            ('start_at', '>=', self.start_date),
            ('start_at', '<=', self.end_date),
            ('user_id.company_id', '=', self.env.user.company_id.id),
            ('config_id', 'in', pos_configs),
            ('config_id.sucursal_id.id', '=', user_sucursal.id),
            ('factura_global', '=', False),
        ])

        # aqui verifico que no haya ordenes con cliente asignado y sin facturar
        '''orders_without_invoicing = []
        for session in sessions_to_invoicing:
            for order in session.order_ids:
                if order.partner_id.id != self.env.user.company_id.invoice_partner_id.id and order.state != 'invoiced' and order.amount_total > 0:
                    orders_without_invoicing.append(order.pos_reference)
        if len(orders_without_invoicing) > 0:
            message = 'Las siguientes ordenes tiene cliente asignado pero no fueron facturadas:\n'
            for ord in orders_without_invoicing:
                message += str(ord) + ',\n'
            raise UserError(message)'''

        opened_sessions = self.env['pos.session'].search([
            ('state', '=', 'opened'),
            ('start_at', '>=', self.start_date),
            ('start_at', '<=', self.end_date),
            ('user_id.company_id', '=', self.env.user.company_id.id),
            ('config_id', 'in', pos_configs),
            ('config_id.sucursal_id.id', '=', user_sucursal.id),
            ('factura_global', '=', False),
        ])

        if opened_sessions:
            raise UserError(
                'Existen sessiones sin cerrar, para continuar con el proceso de facturacion debes cerrar todas las sesiones.')

        # Creacion de la factura

        # obtengo las ordenes a facturar
        orders = self.env['pos.order'].search(
            [('date_order', '>=', self.start_date), ('date_order', '<=', self.end_date), ('state', '!=', 'invoiced'),
             ('amount_total', '>', 0), ('sucursal_id', '=', self.env.user.sucursal_id.id)])

        # si no hay ordenes se termina el proceso
        if len(orders) == 0:
            _logger.warning("Termino el proceso, no hay ordenes por facturar.")
            for session in sessions_to_invoicing:
                session.write({
                    'factura_global': True,
                }
                )
            raise UserError(
                'No hay pedidos que facturar.')
            return

        # Genero la factura global
        Invoice = self.env['account.move'].create(self._prepare_global_invoice(pos_configs, orders))

        for line in Invoice.line_ids:
            if line.currency_id:
                line._onchange_currency()
        Invoice._recompute_dynamic_lines(recompute_all_taxes=False)
        Invoice._check_balanced()

        for order in orders:
            order.write({
                'account_move': Invoice.id,
                'state': 'invoiced'
            })
        Invoice.action_post()
        for session in sessions_to_invoicing:
            session.sudo(True).write({
                'factura_global': True,
                'global_invoice_name': Invoice.name,
            })

        return {
            'name': _('Customer Invoice'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'nodestroy': False,
            'target': 'current',
            'res_id': Invoice.id and Invoice.ids[0] or False,
        }

    def _prepare_global_invoice(self, config_ids, orders):
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
            raise UserError('Existe más de un diario de facturas en los puntos de venta a facturar')
        if len(list(set(position_fiscal_ids))) > 1:
            raise UserError('Existe más de una posición fiscal en los puntos de venta a facturar')
        if len(list(set(sucursal_ids))) > 1:
            raise UserError('Existe más de una sucursal en los puntos de venta a facturar')
        if len(list(set(analytic_account_ids))) > 1:
            raise UserError('Existe más de una cuenta analitica en los puntos de venta a facturar')

        payment_term_id = self.env['account.payment.term'].search([('name', '=', 'Immediate Payment')]).id

        if not payment_term_id:
            payment_term_id = 1

        data_invoice = {
            'partner_id': self.env.user.company_id.invoice_partner_id.id,
            'l10n_mx_edi_payment_method_id': int(self.pay_method_id),
            'l10n_mx_edi_usage': self.uso_cfdi_id,
            'user_id': self.env.user.id,
            'team_id': equipo_ventas[0],
            'journal_id': journal_ids[0],
            'currency_id': self.env.user.company_id.currency_id.id,
            'invoice_user_id': self.env.user.id,
            'fiscal_position_id': position_fiscal_ids[0],
            'type': 'out_invoice',
            'company_id': self.env.user.company_id.id,
            # 'l10n_mx_edi_payment_method_id': 1,
            'invoice_date': str(date.today()),  # - timedelta(days=2)),
            'date': str(date.today()),
            'invoice_payment_term_id': payment_term_id,
            # 'date_due': str(date.today()),
            'line_ids': [
            ],
            'invoice_origin': 'Factura Global - ' + str(self.start_date)[0:10] + ' - ' + self.env[
                'res.partner'].browse(
                sucursal_ids[0]).name,
            'invoice_date_due': str(date.today()),
        }

        # Agrego todos los impuestos
        for impuesto in self.env['account.tax'].search(
                [('type_tax_use', '=', 'sale'), ('l10n_mx_cfdi_tax_type', '=', 'Tasa'), ]):
            # ('amount', '>', 0)]):
            if impuesto.cash_basis_transition_account_id:
                data_invoice['line_ids'].append(self._get_info_tax(impuesto.name))

        # Agrego la linea de totales
        data_invoice['line_ids'].append(self._get_line_totals())

        # Agrego las lineas de factura de las ventas
        self._add_invoice_lines(data_invoice, orders)
        return data_invoice

    def _add_invoice_lines(self, data_invoice, orders):
        account_id = self.env['account.account'].search(
            [('name', '=', 'Ventas y/o servicios gravados a la tasa general')]).id

        # Recorro las ordenes para agregarlas a la lista para crear la factura
        for order in orders:
            order_taxes = {}

            # omite las que ya se facturaron
            if order.state == 'invoiced' or order.amount_total <= 0:
                continue

            # reviso que taxes tiene cada linea de pedido
            for orderline in order.lines:
                for tax in orderline.tax_ids:
                    order_taxes[int(tax.amount)] = tax.id

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

                line = []
                line.append(0)
                line.append('')
                line.append({
                    'account_id': account_id,
                    'sequence': 10,
                    'name': description,
                    'quantity': 1,
                    'price_unit': amount_total,
                    'discount': 0,
                    'debit': 0,
                    'credit': subtotal,
                    'amount_currency': 0,
                    'date_maturity': False,
                    'currency_id': False,
                    'partner_id': self.env['res.company'].browse(
                        self.env.user.company_id.id).invoice_partner_id.id,
                    'product_uom_id': 1,
                    'product_id': self.env['res.company'].browse(
                        self.env.user.company_id.id).invoice_product_id.id,
                    'payment_id': False,
                    'tax_ids': [[6, False, [order_taxes.get(order_tax)]]],
                    'tax_base_amount': 0,
                    'tax_exigible': False,
                    'tax_repartition_line_id': False,
                    'tag_ids': [[6, False, []]],
                    'analytic_account_id': order.session_id.config_id.x_cuenta_analitica.id,
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
                })

                for li in data_invoice['line_ids']:
                    if li[2]['name'] == False:
                        price_unit_aux = round(abs(li[2]['price_unit']), 2)
                        debit_aux = li[2]['debit']
                        li[2]['price_unit'] = - round((price_unit_aux + amount_total), 2)
                        li[2]['debit'] = round(debit_aux + amount_total, 2)
                        break

                impuesto = self.env['account.tax'].browse(order_taxes.get(order_tax))
                if impuesto.l10n_mx_cfdi_tax_type == 'Tasa' and impuesto.amount > 0:
                    for li in data_invoice['line_ids']:
                        if li[2]['name'] == impuesto.name:
                            aux_credit = li[2]['credit']
                            aux_price_unit = li[2]['price_unit']
                            aux_tax_base_amount = li[2]['tax_base_amount']

                            li[2]['credit'] = round(aux_credit + (amount_total - subtotal), 2)
                            li[2]['price_unit'] = round(aux_price_unit + (amount_total - subtotal), 2)
                            li[2]['tax_base_amount'] = round(aux_tax_base_amount + subtotal, 2)
                elif impuesto.l10n_mx_cfdi_tax_type == 'Tasa' and impuesto.amount == 0:
                    for li in data_invoice['line_ids']:
                        if li[2]['name'] == impuesto.name:
                            li[2]['quantity'] = 1

                lines = data_invoice['line_ids']
                lines.append(line)

        # borro los impuestos que no son usados
        lineas_borrar = []
        for line in data_invoice['line_ids']:
            if line[2]['name'] and not line[2]['product_id'] and line[2]['credit'] == 0 and line[2][
                'tax_base_amount'] == 0 and line[2]['quantity'] == -1:
                lineas_borrar.append(line)

        # Elimino los imuestos que no fueron utilizados
        for line in lineas_borrar:
            data_invoice['line_ids'].remove(line)

    def _get_line_totals(self):

        # lineas = data_invoice['line_ids']

        totals = [
            0, '',
            {
                'account_id': self.env['res.company'].browse(
                    self.env.user.company_id.id).invoice_partner_id.property_account_receivable_id.id,
                'sequence': 10,
                'name': False,
                'quantity': 1,
                'price_unit': -0,
                'discount': 0,
                'debit': 0,
                'credit': 0,
                'amount_currency': 0,
                'date_maturity': str(date.today()),
                'currency_id': False,
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

    def _get_info_tax(self, etiqueta_impuesto):
        impuesto_def = self.env['account.tax'].search([('name', '=', etiqueta_impuesto)])
        repartition_id = 0
        for imp in impuesto_def.invoice_repartition_line_ids:
            if imp.repartition_type == 'tax':
                repartition_id = imp.id

        if impuesto_def:
            impuesto = [
                0, '',
                {
                    'account_id': impuesto_def.cash_basis_transition_account_id.id,
                    'sequence': 10,
                    'name': impuesto_def.name,
                    'quantity': -1,
                    'price_unit': 0,
                    'discount': 0,
                    'debit': 0,
                    'credit': 0,
                    'amount_currency': 0,
                    'date_maturity': False,
                    'currency_id': False,
                    'partner_id': self.env['res.company'].browse(self.env.user.company_id.id).invoice_partner_id.id,
                    'product_uom_id': False,
                    'product_id': False,
                    'payment_id': False,
                    'tax_ids': [[6, False, []]],
                    'tax_base_amount': 0,
                    'tax_exigible': False,
                    'tax_repartition_line_id': repartition_id,
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
        return impuesto


class smaynota(models.Model):
    _inherit = 'account.move'

    '''@api.model
    def create(self, vals):
        _logger.warning('FUNCION CREATEEEEE')
        _logger.warning(str(vals))
        return super(smaynota, self).create(vals)'''


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
                                      ], 'Metodo de pago', default='1', required=True, readonly=True)

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
                                    ], 'Uso del CFDI', default='G01', required=True, readonly=True)

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
            [('state', '=', 'closed'),
             ('start_at', '>=', self.start_date),
             ('start_at', '<=', self.end_date),
             ('user_id.company_id', '=', self.env.user.company_id.id),
             ('config_id', 'in', pos_configs),
             ('config_id.sucursal_id.id', '=', user_sucursal.id),
             # ('notas_credito_global', '=', False),
             ('factura_global', '=', False)
             ])

        if sessions_without_invoice:
            for session in sessions_without_invoice:
                session.write({
                    'notas_credito_global': True
                })
            raise UserError('Es necesario que primero realices la Facturación Global.')

        sessions_to_invoicing = self.env['pos.session'].search(
            [('state', '=', 'closed'),
             ('start_at', '>=', self.start_date),
             ('start_at', '<=', self.end_date),
             ('user_id.company_id', '=', self.env.user.company_id.id),
             ('config_id', 'in', pos_configs),
             ('config_id.sucursal_id.id', '=', user_sucursal.id),
             ('notas_credito_global', '=', False),
             ])

        if not sessions_to_invoicing:
            raise UserError('No existen sesiones para generar notas de credito en las fechas indicadas')

        # orders = 0
        for session in sessions_to_invoicing:
            refund_orders_without_cr = self.env['pos.order'].search(
                [('session_id', '=', session.id),
                 ('amount_total', '<', 0),
                 ('state', '!=', 'invoiced')])
            # orders += len(refund_orders_without_cr)
            if len(refund_orders_without_cr) == 0:
                session.sudo().write({
                    'notas_credito_global': True
                })

        orders = self.env['pos.order'].search(
            [('date_order', '>=', self.start_date), ('date_order', '<=', self.end_date), ('state', '!=', 'invoiced'),
             ('amount_total', '<', 0), ('sucursal_id', '=', self.env.user.sucursal_id.id)])

        if len(orders) == 0:
            _logger.warning("Termino el proceso, no hay devoluciones por facturar.")
            for session in sessions_to_invoicing:
                session.write({
                    'factura_global': True,
                }
                )
            raise UserError(
                'No hay devoluciones que facturar.')
            return

        '''pos_references = []
        for session in sessions_to_invoicing:
            refund_orders_without_cr = self.env['pos.order'].search(
                [('session_id', '=', session.id),
                 ('amount_total', '<', 0),
                 ('state', '!=', 'invoiced')])
            for refund_order in refund_orders_without_cr:
                pos_references.append(refund_order.pos_reference)'''

        invoices_to_refund = {}
        for order in orders:
            _logger.warning(str(order.pos_reference))
            '''invoice_id = self.env['account.move.line'].search(
                [('name', 'like', order.pos_reference),
                 ('move_id.type', '=', 'out_invoice'),
                 ], limit=1, order='id asc').move_id.id'''
            self.env.cr.execute('''
            select am.id as ID
            from account_move_line aml
            join account_move am
                on am.id = aml.move_id
            where aml.name like '%''' + str(order.pos_reference) + '''%'
                and am.type='out_invoice'
            order by am.id asc
            limit 1
            
            ''')
            invoice_id = self.env.cr.dictfetchone()['id']
            _logger.warning(str(invoice_id))
            if invoice_id:
                if invoice_id not in invoices_to_refund:
                    invoices_to_refund[invoice_id] = []
                    invoices_to_refund[invoice_id].append(order.id)
                else:
                    invoices_to_refund[invoice_id].append(order.id)

        credit_note = None
        for factura_id in invoices_to_refund.keys():
            _logger.warning('Aqui empiezo la factura' + str(factura_id))
            data_invoice = self.prepare_invoice(factura_id)
            data_invoice['line_ids'].append(self._get_line_totals(factura_id))
            data_invoice = self.add_tax_line(data_invoice, invoice_id)
            data_invoice = self._add_invoice_lines(data_invoice, invoice_id, invoices_to_refund[factura_id])
            _logger.warning('NOTA DE CREITOOOOO' + str(data_invoice))

            credit_note = self.env['account.move'].create(data_invoice)
            _logger.warning('ESTO ES LA SALIDA DE LA FACTURA PARA GENERARLa')
            _logger.warning(str(data_invoice))
            _logger.warning(str(credit_note))

            for line in credit_note.line_ids:
                if line.currency_id:
                    line._onchange_currency()
            credit_note._recompute_dynamic_lines(recompute_all_taxes=False)
            credit_note._check_balanced()

        if credit_note:
            return {
                'name': _('Customer Invoice'),
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('account.view_move_form').id,
                'res_model': 'account.move',
                'context': "{'type':'out_invoice'}",
                'type': 'ir.actions.act_window',
                'nodestroy': False,
                'target': 'current',
                'res_id': credit_note.id and credit_note.ids[0] or False,
            }

    def add_tax_line(self, data_invoice, invoice_id):
        # aqui
        taxe_ids = self.env['account.move.line'].search(
            [('product_id', '=', None), ('tax_line_id', '!=', None), ('move_id', '=', invoice_id)])
        for tax in taxe_ids:
            existe_tax = False
            for line in data_invoice['line_ids']:
                if line[2]['name'] == tax.name:
                    existe_tax = True
                    break

            if not existe_tax:
                tax_line = (
                    0,
                    0,
                    {
                        'move_id': tax.move_id.id,
                        'account_id': tax.account_id.id,
                        'sequence': 0,
                        'name': tax.name, 'quantity': - 1.0,
                        # 'price_unit': 9601.54,
                        'price_unit': 0.00,
                        'discount': 0.0,
                        # 'debit': 9601.54,
                        'debit': 0.00,
                        'credit': 0.0,
                        'amount_currency': -0.0,
                        # 'price_subtotal': 9601.54,
                        'price_subtotal': 0.00,
                        # 'price_total': 9601.54,
                        'price_total': 0.00,
                        'blocked': False,
                        'date_maturity': str(date.today()),
                        'currency_id': False,
                        'partner_id': self.env.user.company_id.invoice_partner_id.id,
                        'product_uom_id': False,
                        'product_id': False,
                        # 'tax_ids': [(6, 0, [1, 13])],
                        'tax_ids': [(6, 0, [])],
                        # 'tax_base_amount': 60009.71,
                        'tax_base_amount': 0.00,
                        'tax_exigible': False,
                        'tax_repartition_line_id': tax.tax_repartition_line_id.id,
                        'tag_ids': [(6, 0, [])],
                        'analytic_account_id': tax.analytic_account_id.id,
                        'analytic_tag_ids': [(6, 0, [])],
                        'recompute_tax_line': False,
                        'display_type': False,
                        'is_rounding_line': False,
                        'exclude_from_invoice_tab': True,
                        'purchase_line_id': False,
                        'is_anglo_saxon_line': False,
                        'predict_from_name': False,
                        'predict_override_default_account': False,
                        'expected_pay_date': False,
                        'internal_note': False,
                        'next_action_date': False,
                        'l10n_mx_edi_qty_umt': 0.0,
                        'l10n_mx_edi_price_unit_umt': 0.0,
                        'sale_line_ids': [(6, None, [])]
                    }
                )
                data_invoice['line_ids'].append(tax_line)
        return data_invoice

    def _add_invoice_lines(self, data_invoice, invoice_id, order_ids):
        orders = self.env['pos.order'].search([('id', 'in', order_ids)])
        for order in orders:
            order_taxes = {}

            # omite las que ya se facturaron
            if order.state == 'invoiced' or order.amount_total >= 0:
                continue

            # reviso que taxes tiene cada linea de pedido
            for orderline in order.lines:
                for tax in orderline.tax_ids:
                    order_taxes[int(tax.amount)] = tax.id

            for order_tax in order_taxes:
                description = order.pos_reference + '_' + str(order_tax)
                amount_total = 0
                subtotal = 0
                for orderline_2 in order.lines:
                    if order_taxes.get(order_tax) == orderline_2.tax_ids.id:
                        amount_total += orderline_2.price_subtotal_incl
                        subtotal += orderline_2.price_subtotal

                if amount_total >= 0:
                    continue

                # aqui debo de guardar cada linea de factura

                _original_line = self.env['account.move.line'].search(
                    [('move_id', '=', invoice_id), ('move_id.type', '=', 'out_invoice'), ('name', 'like', description)],
                    limit=1, order='id asc')

                line = []
                line.append(0)
                line.append(0)
                line.append({
                    'move_id': invoice_id,
                    # 'account_id': account_id,
                    'account_id': _original_line.account_id.id,
                    'sequence': _original_line.sequence,
                    'name': description,
                    'quantity': 1.0,
                    'price_unit': round(abs(amount_total), 2),
                    'discount': 0.0,
                    'debit': round(abs(subtotal), 2),
                    'credit': 0.0,  # abs(subtotal),
                    'amount_currency': 0.0,
                    'price_subtotal': abs(subtotal),
                    'price_total': abs(amount_total),
                    'blocked': False,
                    'date_maturity': str(date.today()),
                    'currency_id': False,
                    'partner_id': self.env['res.company'].browse(
                        self.env.user.company_id.id).invoice_partner_id.id,
                    'product_uom_id': _original_line.product_uom_id.id,
                    'product_id': self.env['res.company'].browse(
                        self.env.user.company_id.id).invoice_product_id.id,
                    'tax_ids': [[6, False, [order_taxes.get(order_tax)]]],
                    'tax_base_amount': 0.0,
                    'tax_exigible': False,
                    'tax_repartition_line_id': False,
                    'tag_ids': [[6, False, []]],
                    'analytic_account_id': order.session_id.config_id.x_cuenta_analitica.id,
                    'analytic_tag_ids': [[6, False, []]],
                    'recompute_tax_line': False,
                    'display_type': False,
                    'is_rounding_line': False,
                    'exclude_from_invoice_tab': False,
                    'purchase_line_id': False,
                    'is_anglo_saxon_line': False,
                    'predict_from_name': False,
                    'predict_override_default_account': False,
                    'expected_pay_date': False,
                    'internal_note': False,
                    'next_action_date': False,
                    'l10n_mx_edi_qty_umt': 0.0,
                    'l10n_mx_edi_price_unit_umt': 0.0,
                    'sale_line_ids': [(6, None, [])]
                })

                for li in data_invoice['line_ids']:
                    if li[2]['name'] == False:
                        price_unit_aux = round(abs(li[2]['price_unit']), 2)
                        debit_aux = li[2]['debit']
                        credit_aux = li[2]['credit']
                        # li[2]['price_unit'] = - round((price_unit_aux + amount_total), 2)
                        # li[2]['debit'] = round(debit_aux + amount_total, 2)
                        li[2]['credit'] = round(abs(credit_aux) + abs(amount_total), 2)
                        break

                impuesto = self.env['account.tax'].browse(order_taxes.get(order_tax))
                if impuesto.l10n_mx_cfdi_tax_type == 'Tasa' and impuesto.amount > 0:
                    for li in data_invoice['line_ids']:
                        if li[2]['name'] == impuesto.name.replace(' (POS)', ''):
                            aux_credit = abs(li[2]['credit'])
                            aux_price_unit = abs(li[2]['price_unit'])
                            aux_tax_base_amount = abs(li[2]['tax_base_amount'])

                            li[2]['debit'] = round(abs(aux_credit) + (abs(amount_total) - abs(subtotal)), 2)
                            li[2]['price_unit'] = round(abs(aux_price_unit) + (abs(amount_total) - abs(subtotal)), 2)
                            li[2]['tax_base_amount'] = round(abs(aux_tax_base_amount) + abs(subtotal), 2)
                            li[2]['quantity'] = 1
                elif impuesto.l10n_mx_cfdi_tax_type == 'Tasa' and impuesto.amount == 0:
                    for li in data_invoice['line_ids']:
                        if li[2]['name'] == impuesto.name:
                            li[2]['quantity'] = 1

                data_invoice['line_ids'].append(tuple(line))

        # borro los impuestos que no son usados
        lineas_borrar = []
        for line in data_invoice['line_ids']:
            if line[2]['name'] and not line[2]['product_id'] and line[2]['credit'] == 0 and line[2][
                'tax_base_amount'] == 0 and line[2]['quantity'] == -1:
                lineas_borrar.append(line)

        # Elimino los imuestos que no fueron utilizados
        for line in lineas_borrar:
            data_invoice['line_ids'].remove(line)

        return data_invoice

    def prepare_invoice(self, invoice_id):
        invoice_to_refund = self.env['account.move'].browse(invoice_id)
        payment_term_id = self.env['account.payment.term'].search([('name', '=', 'Immediate Payment')]).id

        if not payment_term_id:
            payment_term_id = 1
        data_invoice = {
            'invoice_origin': 'Nota de Credito Global : ' + str(self.start_date)[0:10] + ' - ' + self.sucursal_id,
            'date': str(date.today()),
            'invoice_date': str(date.today()),
            'journal_id': invoice_to_refund.journal_id.id,
            'invoice_payment_term_id': payment_term_id,
            'auto_post': False,
            'invoice_user_id': invoice_to_refund.create_uid.id,
            'campaign_id': False,
            'medium_id': False,
            'source_id': False,
            'type': 'out_refund',
            'reversed_entry_id': invoice_to_refund.id,
            'state': 'draft',
            'narration': False,
            'to_check': False,
            'currency_id': invoice_to_refund.currency_id.id,
            'partner_id': self.env.user.company_id.invoice_partner_id.id,
            'tax_cash_basis_rec_id': False,
            'fiscal_position_id': invoice_to_refund.fiscal_position_id.id,
            # 'invoice_origin': invoice_to_refund.invoice_origin,
            'invoice_partner_bank_id': invoice_to_refund.invoice_partner_bank_id.id,
            'invoice_incoterm_id': False,
            'invoice_vendor_bill_id': False,
            'invoice_source_email': False,
            'invoice_cash_rounding_id': False,
            'duplicated_vendor_ref': False,
            'purchase_vendor_bill_id': False,
            'purchase_id': False,
            'stock_move_id': False,
            'release_to_pay_manual': False,
            'force_release_to_pay': False,
            'transfer_model_id': False,
            'is_tax_closing': False,
            'tax_report_control_error': False,
            'l10n_mx_edi_partner_bank_id': False,
            'l10n_mx_edi_payment_method_id': invoice_to_refund.l10n_mx_edi_payment_method_id.id,
            'l10n_mx_edi_usage': invoice_to_refund.l10n_mx_edi_usage,
            'l10n_mx_edi_cer_source': False,
            'team_id': invoice_to_refund.team_id.id,
            'partner_shipping_id': False,
            'l10n_mx_closing_move': False,
            'line_ids': []
        }
        return data_invoice

    def _get_line_totals(self, invoice_id):
        invoice_to_refund = self.env['account.move'].browse(invoice_id)
        invoice_totals_line = self.env['account.move.line'].search(
            [('product_id', '=', None), ('tax_line_id', '=', None), ('move_id', '=', invoice_id)])
        totals = [
                     0,
                     0,
                     {
                         'move_id': invoice_totals_line.move_id.id,
                         'account_id': invoice_totals_line.account_id.id,
                         'sequence': 0,
                         'name': False,
                         'quantity': 1.0,
                         'price_unit': 0.0,
                         'discount': 0.0,
                         'debit': 0.0,
                         # 'credit': 120339.87,
                         'credit': 0.00,
                         'amount_currency': -0.0,
                         'price_subtotal': 0.0,
                         'price_total': 0.0,
                         'blocked': False,
                         'date_maturity': str(date.today()),
                         'currency_id': False,
                         'partner_id': self.env.user.company_id.invoice_partner_id.id,
                         'product_uom_id': False,
                         'product_id': False,
                         'tax_ids': [(6, 0, [])],
                         'tax_base_amount': 0.0,
                         'tax_exigible': True,
                         'tax_repartition_line_id': False,
                         'tag_ids': [(6, 0, [])],
                         'analytic_account_id': False,
                         'analytic_tag_ids': [(6, 0, [])],
                         'recompute_tax_line': False,
                         'display_type': False,
                         'is_rounding_line': False,
                         'exclude_from_invoice_tab': True,
                         'purchase_line_id': False,
                         'is_anglo_saxon_line': False,
                         'predict_from_name': False,
                         'predict_override_default_account': False,
                         'expected_pay_date': False,
                         'internal_note': False,
                         'next_action_date': False,
                         'l10n_mx_edi_qty_umt': 0.0,
                         'l10n_mx_edi_price_unit_umt': 0.0,
                         'sale_line_ids': [(6, None, [])]
                     }],
        return tuple(totals[0])

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
