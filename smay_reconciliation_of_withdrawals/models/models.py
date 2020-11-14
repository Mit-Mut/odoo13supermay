# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, date, time, timedelta
import time
import pytz

_logger = logging.getLogger(__name__)


class SmayReconciliationWithdrawals(models.Model):
    _name = 'conciliation.withdrawals'
    _description = 'Guarda las conciliaciones de ventas con depositos en el banco'

    # One2many fields
    withdraw_line_ids = fields.One2many('conciliation.withdrawals.line', 'reconciliation_withdraw_id',
                                        'Retiros de Caja')
    card_payment_ids = fields.One2many('conciliation.payments.card', 'conciliation_id', 'Pagos con tarjeta')
    bank_deposit_ids = fields.One2many('conciliation.bank.deposit', 'conciliation_id', 'Depositos bancarios')
    faltante_ids = fields.One2many('conciliation.missed.cash', 'reconciliation_withdraw_id', 'Faltantes de cajero')
    sobrantes_ids = fields.One2many('conciliacion.sobrante.efectivo', 'conciliation_id', 'Sobrantes de cajero')
    refund_ids = fields.One2many('conciliation.refunds', 'conciliation_id', 'Devoluciones')
    gasto_ids = fields.One2many('conciliation.gastos', 'conciliation_id', 'Gastos')
    prestamo_ids = fields.One2many('conciliation.prestamos', 'conciliation_id', 'Prestamos')

    # normal fields
    start_date = fields.Datetime(string="Fecha de inicio", required=True, default=lambda self: self.get_date('START'))
    end_date = fields.Datetime(string="Fecha Final", required=True, default=lambda self: self.get_date('END'))
    validate_retirements_date = fields.Datetime('Fecha de validación de los retiros conciliados')
    validate_deposits_date = fields.Datetime('Fecha de validación de los depositos bancarios')
    comments = fields.Text(string="Comentarios")
    name = fields.Char(default='new', string='Nombre')
    state = fields.Selection([
        ('nuevo', 'Nuevo'),
        ('borrador', 'Borrador'),
        ('retiros_validados', 'Retiros Validados'),
        ('deposito_validado', 'Deposito Validado')
    ], default='nuevo', string='Estado')

    id_withdraw_sucursal = fields.Integer('ID Retiro por Sucursal', default=0)

    # Many2one fields
    sucursal_id = fields.Many2one('res.partner', 'Sucursal', default=lambda self: self.get_sucursal(), readonly=True)
    validate_retirements_uid = fields.Many2one('res.users', 'Usuario que valido retiros conciliados')
    validate_deposits_uid = fields.Many2one('res.users', 'Usuario que valido depositos bancarios')

    '''total_retiros = fields.Float(string='Total Retiros', compute='_compute_all_totals', store=True)
    total_conciliado = fields.Float(string='Total Conciliado', compute='_compute_all_totals', store=True)
    total_diff = fields.Float(string='Total Diferencia', compute='_compute_all_totals', store=True)
    deposit_total = fields.Float(string='Total Depositados', compute='_compute_all_totals', store=True)

    # total_card_payments = fields.Float(string='Total Pagos Tarjeta', compute='_compute_all_totals', store=True)
    total_conciliado_card_payments = fields.Float(string='Total Conciliado Tarjeta', compute='_compute_all_totals',
                                                  store=True)
    total_diff_card_payments = fields.Float(string='Total Diferencia Tarjeta', compute='_compute_all_totals',
                                            store=True)

    total_faltantes = fields.Float(string='Total Faltantes', compute='_compute_all_totals', store=True)

    gran_total = fields.Float(string='Gran Total', compute='_compute_all_totals', store=True)
    '''
    total_conciliado = fields.Float(string='Total Conciliado', default=0, store=True)
    total_gastos = fields.Float(string='Total Gastos', default=0, store=True)
    total_prestamos = fields.Float(string='Total Prestamos', default=0, store=True)
    total_conciliado_card_payments = fields.Float(string='Total Conciliado Tarjeta', default=0,
                                                  store=True)
    total_faltantes = fields.Float(string='Total Faltantes', default=0, store=True)
    total_sobrantes = fields.Float(string='Total de Sobrantes', default=0, store=True)

    total_faltantes_cajeros = fields.Float(string='Total Faltantes Cajeros', default=0, store=True)
    total_sobrantes_cajeros = fields.Float(string='Total de Sobrantes Cajeros', default=0, store=True)

    total_devoluciones = fields.Float(string='Total de Devoluciones', default=0, store=True)
    # deposit_total = fields.Float(string='Total Depositados', default=0, store=True)
    deposit_total = fields.Float(string='Total Depositados', compute='_compute_deposite_totals', store=True)
    total_conciliado_banco = fields.Float(string='Total en Banco', compute='_compute_deposite_totals', store=True)
    total_diferencia_depositos_banco = fields.Float(string='Total Diferencia en Banco', default=0,
                                                    store=True)
    gran_total = fields.Float(string='Gran Total', default=0, store=True)
    total_venta_bruta = fields.Float(string='Venta Bruta', default=0, store=True)
    total_venta_neta = fields.Float(string='Venta Neta', default=0, store=True)

    total_diferencia_banco = fields.Float(string='Diferencia en deposito', compute='_compute_deposite_totals',
                                          store=True)

    # no se utilizan
    total_retiros = fields.Float(string='Total Retiros', default=0)
    total_diff = fields.Float(string='Total Diferencia', default=0)
    total_diff_card_payments = fields.Float(string='Total Diferencia Tarjeta', default=0)

    ######
    @api.depends('bank_deposit_ids.deposited_amount', 'bank_deposit_ids.deposito_validado_en_banco')  # ,
    # 'total_conciliado_banco', 'total_diferencia_banco')
    def _compute_deposite_totals(self):
        for conciliacion in self:
            conciliacion.deposit_total = 0
            conciliacion.total_conciliado_banco = 0
            for deposito in conciliacion.bank_deposit_ids:
                conciliacion.deposit_total += deposito.deposited_amount
                conciliacion.total_conciliado_banco += deposito.deposito_validado_en_banco
            conciliacion.total_diferencia_banco = conciliacion.total_conciliado_banco - conciliacion.gran_total

    def get_date(self, label):
        default_datetime = ''

        if label == 'START':
            default_datetime = str(
                datetime.strptime(str(date.today() - timedelta(days=1)) + ' 00:00:00', "%Y-%m-%d %H:%M:%S"))
        if label == 'END':
            default_datetime = str(
                datetime.strptime(str(date.today() - timedelta(days=1)) + ' 23:59:59', "%Y-%m-%d %H:%M:%S"))

        if default_datetime != '':
            local = pytz.timezone(self.env.user.tz)
            fecha = datetime.strptime(default_datetime, "%Y-%m-%d %H:%M:%S")
            local_dt = local.localize(fecha).astimezone(pytz.utc)
            return str(local_dt)[0:19]
        return '2017-02-02 17:30:00'

    # @api.multi
    def unlink(self):
        for record in self:
            if record.state == 'retiros_validados' or record.state == 'deposito_validado':
                raise ValidationError('Solo se pueden eliminar las conciliaciones que son borradores.')
        return super(SmayReconciliationWithdrawals, record).unlink()

    def update_totals_managers(self):
        for conciliacion in self:

            # calcula total de los depositos ingresados por el conciliador
            conciliacion.deposit_total = 0
            for line in conciliacion.bank_deposit_ids:
                conciliacion.deposit_total += line.deposited_amount

            # calcula el total de lo verificado en el banco
            conciliacion.total_conciliado_banco = 0
            for line in conciliacion.bank_deposit_ids:
                conciliacion.total_conciliado_banco += line.deposito_validado_en_banco

                # recalcula el total de ventas
                # if self.env.user.is_manager:
            ventas = self.env['pos.order'].search(
                [('date_order', '>=', self.start_date), ('date_order', '<=', self.end_date),
                 ('amount_total', '>', 0),
                 ('sucursal_id', '=', conciliacion.sucursal_id.id)
                 ])

            conciliacion.total_venta_bruta = 0
            for venta in ventas:
                conciliacion.total_venta_bruta += venta.amount_total

            conciliacion.total_diferencia_depositos_banco = conciliacion.total_conciliado_banco - conciliacion.deposit_total

            for faltante in conciliacion.faltante_ids:
                if faltante.commentary == 'Diferencia presentada en los depositos bancarios':
                    faltante.unlink()

            for sobrante in conciliacion.sobrantes_ids:
                if sobrante.commentary == 'Diferencia presentada en los depositos bancarios':
                    sobrante.unlink()

            if conciliacion.total_diferencia_banco < 0:
                # creo el registro en faltantes a nombre del conciliador
                vals = {}
                vals['reconciliation_withdraw_id'] = conciliacion.id
                vals['cajero_id'] = conciliacion.create_uid.name
                vals['amount'] = abs(conciliacion.total_diferencia_banco)
                vals['commentary'] = 'Diferencia presentada en los depositos bancarios'
                self.env['conciliation.missed.cash'].create(vals)
            elif conciliacion.total_diferencia_banco > 0:
                # creo el registro en sobrantes
                vals = {}
                vals['conciliation_id'] = conciliacion.id
                vals['cajero_id'] = conciliacion.create_uid.name
                vals['amount'] = abs(conciliacion.total_diferencia_banco)
                vals['commentary'] = 'Diferencia presentada en los depositos bancarios'
                self.env['conciliacion.sobrante.efectivo'].create(vals)

            '''diferencia_conciliado_depositado = conciliacion.deposit_total - conciliacion.total_conciliado

            for faltante in conciliacion.faltante_ids:
                if faltante.commentary == 'Diferencia en conciliado vs depositado':
                    faltante.unlink()

            for sobrante in conciliacion.sobrantes_ids:
                if sobrante.commentary == 'Diferencia en conciliado vs depositado':
                    sobrante.unlink()

            if conciliacion.deposit_total - conciliacion.total_conciliado < 0:
                # creo el registro en faltantes a nombre del conciliador
                vals = {}
                vals['reconciliation_withdraw_id'] = conciliacion.id
                vals['cajero_id'] = conciliacion.create_uid.name
                vals['amount'] = abs(diferencia_conciliado_depositado)
                vals['commentary'] = 'Diferencia en conciliado vs depositado'
                self.env['conciliation.missed.cash'].create(vals)
            elif conciliacion.deposit_total - conciliacion.total_conciliado > 0:
                # creo el registro en sobrantes
                vals = {}
                vals['conciliation_id'] = conciliacion.id
                vals['cajero_id'] = conciliacion.create_uid.name
                vals['amount'] = abs(diferencia_conciliado_depositado)
                vals['commentary'] = 'Diferencia en conciliado vs depositado'
                self.env['conciliacion.sobrante.efectivo'].create(vals)'''

            conciliacion.total_faltantes = 0
            for line in conciliacion.faltante_ids:
                conciliacion.total_faltantes += line.amount

            conciliacion.total_sobrantes = 0
            for line in conciliacion.sobrantes_ids:
                conciliacion.total_sobrantes += line.amount

            '''conciliacion.total_venta_neta = conciliacion.total_venta_bruta - abs(conciliacion.total_devoluciones)

            conciliacion.total_diferencia_banco = conciliacion.total_conciliado_banco - conciliacion.gran_total'''

    # @api.multi
    def get_sucursal(self):
        if not self.env.user.sucursal_id:
            raise UserError(
                'El usuario no tiene sucursal Asignada. Contacta a un administrador para la correcta configuración de tu cuenta.')
        return self.env.user.sucursal_id.id

    def print_report(self):
        self.ensure_one()
        self.env.ref('smay_reconciliation_of_withdrawals.bank_conciliation').report_action(self.id)
        return self.env.ref('smay_reconciliation_of_withdrawals.bank_conciliation').report_action(self.id)

    @api.model
    def create(self, vals):
        if not self.env.user.is_manager:
            raise UserError('Solo los ENCARGADOS/CONCILIADORES pueden crear registros.')

        id_conciliacion = self.search([('sucursal_id', '=', self.env.user.sucursal_id.id)], order="id desc",
                                      limit=1).id_withdraw_sucursal
        if not id_conciliacion:
            vals['id_withdraw_sucursal'] = 1
        else:
            vals['id_withdraw_sucursal'] = id_conciliacion + 1

        res = super(SmayReconciliationWithdrawals, self).create(vals)
        res.write({'name': 'Conciliación ' + str(self.env.user.sucursal_id.name).replace('Sucursal', '') + ' ' + str(
            res.id_withdraw_sucursal)})
        if res.state == 'nuevo':
            res.write({'state': 'borrador'})
        ##Automatización de la conciliación
        retiros_conciliar = self.env['account.bank.statement.line'].search(
            [('create_date', '>=', vals['start_date']), ('create_date', '<=', vals['end_date']),
             ('x_sucursal_id', '=', self.env.user.sucursal_id.id), ('name', 'in', ['retiro'])])

        if not retiros_conciliar:
            raise UserError('No existen retiros para conciliar en las fechas indicadas.')

        rets = []
        for ret in retiros_conciliar:
            rets.append(ret.sequence_cashbox_out_id)

        retiros_conciliados = self.env['conciliation.withdrawals.line'].search(
            [('reconciliation_withdraw_id.sucursal_id', '=', self.env.user.sucursal_id.id),
             ('retirement_id', 'in', rets), ('reconciliation_withdraw_id', '!=', res.id)])

        if retiros_conciliados:
            raise UserError("Hay retiros de las fechas ingresadas que ya fueron conciliados.")

        ultimo_folio = self.env['conciliation.withdrawals.line'].search(
            [('reconciliation_withdraw_id.sucursal_id', '=', self.env.user.sucursal_id.id)], order='retirement_id desc',
            limit=1).retirement_id

        if ultimo_folio:
            if sorted(rets)[0] - ultimo_folio > 1:
                raise UserError('Existen folios sin conciliar anteriores a las fechas ingresadas.')

        total_retiros = 0
        for ret in retiros_conciliar:
            line = {}
            line['retirement_id'] = ret.sequence_cashbox_out_id
            line['total_amount'] = abs(ret.amount)

            if ret.name == 'retiro':
                line['real_amount'] = abs(ret.amount)
                total_retiros += abs(ret.amount)
                line['difference'] = 0
                '''else:
                    line['real_amount'] = 0
                    line['difference'] = abs(ret.amount)'''

                line['commentary'] = ret.comment
                line['reconciliation_withdraw_id'] = res.id
                self.env['conciliation.withdrawals.line'].create(line)
        res.write({
            'total_conciliado': total_retiros
        })

        # elimino los que pertenecen a otras conciliaciones
        retiros = self.env['conciliation.withdrawals.line'].search(
            [('reconciliation_withdraw_id.sucursal_id', '=', self.env.user.sucursal_id.id),
             ('retirement_id', 'in', rets), ('reconciliation_withdraw_id', '!=', res.id)])

        for ret in retiros:
            for retiro in res.withdraw_line_ids:
                if ret.retirement_id == retiro.retirement_id:
                    retiro.unlink()

        ## LLenado de lso gastos

        gastos = self.env['account.bank.statement.line'].search(
            [('create_date', '>=', vals['start_date']), ('create_date', '<=', vals['end_date']),
             ('x_sucursal_id', '=', self.env.user.sucursal_id.id), ('name', 'in', ['gasto'])])

        total_gastos = 0
        for gasto in gastos:
            line = {}
            line['retirement_id'] = gasto.sequence_cashbox_out_id
            line['amount'] = abs(gasto.amount)
            total_gastos += abs(gasto.amount)
            line['description'] = gasto.comment
            line['conciliation_id'] = res.id
            self.env['conciliation.gastos'].create(line)
        res.write({
            'total_gastos': total_gastos
        })

        ###temina llenado de gatos

        ## LLenado de lso gastos
        prestamos = self.env['account.bank.statement.line'].search(
            [('create_date', '>=', vals['start_date']), ('create_date', '<=', vals['end_date']),
             ('x_sucursal_id', '=', self.env.user.sucursal_id.id), ('name', 'in', ['prestamo'])])

        total_prestamos = 0
        for prestamo in prestamos:
            line = {}
            line['retirement_id'] = prestamo.sequence_cashbox_out_id
            line['amount'] = abs(prestamo.amount)
            total_prestamos += abs(prestamo.amount)
            line['description'] = prestamo.comment
            line['conciliation_id'] = res.id
            self.env['conciliation.prestamos'].create(line)
        res.write({
            'total_prestamos': total_prestamos
        })
        ###temina llenado de gatos

        devoluciones = self.env['pos.order'].search(
            [('create_date', '>=', vals['start_date']), ('create_date', '<=', vals['end_date']),
             ('sucursal_id', '=', self.env.user.sucursal_id.id), ('is_refund', '=', True),
             ('amount_total', '<', 0)],
            order='user_id asc')

        total_devoluciones = 0
        for devolucion in devoluciones:
            dev = {}
            dev['conciliation_id'] = res.id
            dev['cajero_id'] = devolucion.user_id.id
            dev['motivo_devolucion'] = devolucion.x_motivo_devolucion
            dev['pos_reference'] = devolucion.pos_reference
            dev['amount'] = devolucion.amount_total
            total_devoluciones += devolucion.amount_total
            self.env['conciliation.refunds'].create(dev)
        res.write({
            'total_devoluciones': total_devoluciones
        })

        if len(res.withdraw_line_ids) == 0:
            raise UserError('No hay retiros por conciliar en las fechas indicadas.')

        # Pagos con tarjeta
        sessions = self.env['pos.session'].search(
            [('create_date', '>=', vals['start_date']),
             ('create_date', '<=', vals['end_date'])])

        total_pago_tajeta = 0
        total_sobrantes = 0
        total_faltantes = 0
        for session in sessions:
            total_efectivo = 0
            for order in session.order_ids:
                vals = {}
                # for payment in order.statement_ids:
                for payment in order.payment_ids:
                    # if payment.journal_id.name.upper() == 'TARJETA DE CRÉDITO':
                    if payment.payment_method_id.uso_terminal_smay:
                        vals['conciliation_id'] = res.id
                        vals['order_reference'] = order.pos_reference.replace('Pedido ', '').replace('Order ', '')
                        vals['amount'] = payment.amount
                        total_pago_tajeta += payment.amount
                        vals['cajero'] = order.user_id.partner_id.name
                        vals['session'] = session.name
                        self.env['conciliation.payments.card'].create(vals)
                    if payment.payment_method_id.name.upper() == 'EFECTIVO':
                        total_efectivo += payment.amount

            retiros_por_session = self.env['account.bank.statement.line'].search(
                [('ref', '=', session.name), ('name', 'in', ['prestamo', 'retiro', 'gasto']),
                 ('x_sucursal_id', '=', self.env.user.sucursal_id.id)])

            total_retiros = 0
            for retiro in retiros_por_session:
                total_retiros += abs(retiro.amount)

            diferencia = total_efectivo - total_retiros
            if diferencia > 0:
                vals = {}
                vals['reconciliation_withdraw_id'] = res.id
                vals['cajero_id'] = session.user_id.partner_id.name
                vals['amount'] = diferencia
                total_faltantes += diferencia
                vals['commentary'] = session.name
                self.env['conciliation.missed.cash'].create(vals)

            # diferencia = total_efectivo - total_retiros
            if diferencia < 0:
                vals = {}
                vals['conciliation_id'] = res.id
                vals['cajero_id'] = session.user_id.partner_id.name
                vals['amount'] = abs(diferencia)
                total_sobrantes += abs(diferencia)
                vals['commentary'] = session.name
                self.env['conciliacion.sobrante.efectivo'].create(vals)

        ventas = self.env['pos.order'].search(
            [('date_order', '>=', res.start_date), ('date_order', '<=', res.end_date), ('amount_total', '>', 0),
             ('sucursal_id', '=', res.sucursal_id.id)
             ])

        total_venta_bruta = 0
        for venta in ventas:
            total_venta_bruta += venta.amount_total

        res.write({
            'total_conciliado_card_payments': total_pago_tajeta,
            'total_faltantes': total_faltantes,
            'total_sobrantes': total_sobrantes,
            'total_venta_bruta': total_venta_bruta,
            'total_venta_neta': total_venta_bruta - abs(total_devoluciones),
            'gran_total': (total_venta_bruta - abs(
                total_devoluciones) - total_pago_tajeta - total_gastos - total_prestamos - total_faltantes + total_sobrantes),
            'total_faltantes_cajeros': total_faltantes,
            'total_sobrantes_cajeros': total_sobrantes,

        })

        #####
        self.validate_lines()
        # self._compute_all_totals()
        return res

    # @api.multi
    def write(self, vals):
        res = super(SmayReconciliationWithdrawals, self).write(vals)
        self.validate_lines()
        return res

    # @api.multi
    def validate_lines(self):
        # return
        # elimina las lineas en cero
        for line in self.withdraw_line_ids:
            if line.retirement_id <= 0 or line.real_amount < 0:
                line.unlink()

        # elimina las lineas repetidas en la misma conciliacion
        for line in self.withdraw_line_ids:
            exists_line = False

            for line_aux in self.withdraw_line_ids:
                if line.id != line_aux.id and line.retirement_id == line_aux.retirement_id:
                    exists_line = True
                    break
            if exists_line:
                line_aux.total_amount = line.total_amount
                line.unlink()

        # revisa que la el folio no exista en otra conciliacion
        for line in self.withdraw_line_ids:
            conciliation_lines = self.env['conciliation.withdrawals.line'].search(
                [('retirement_id', '=', line.retirement_id),
                 ('reconciliation_withdraw_id.sucursal_id', '=', self.sucursal_id.id),
                 ('reconciliation_withdraw_id', '!=', self.id)])
            # raise UserError(str(conciliation_lines))
            for conciliation in conciliation_lines:
                raise UserError(
                    'El folio ' + str(conciliation.retirement_id) + ' ya esta asignado en la conciliacion ' + str(
                        conciliation.reconciliation_withdraw_id.name))

        # actualiaco las lineas de retiros
        for line in self.withdraw_line_ids:
            line_aux = self.env['account.bank.statement.line'].search(
                [('sequence_cashbox_out_id', '>', '0'), ('sequence_cashbox_out_id', '=', line.retirement_id),
                 ('x_sucursal_id', '=', line.reconciliation_withdraw_id.sucursal_id.id)],
                order='sequence_cashbox_out_id asc', limit=1)
            if line.retirement_id in [907]:
                continue
            line.write({
                'total_amount': abs(line_aux.amount),
                'real_amount': line.real_amount,
                'difference': line.real_amount - abs(line_aux.amount),
            })

        # aqui van las validaciones de los pagos con tarjeta
        # alimino las que estan repetidas en la mis conciliacion
        # raise UserError(str(self.card_payment_ids))
        for order_with_card in self.card_payment_ids:
            exists_line = False

            for order_with_card_aux in self.card_payment_ids:
                if order_with_card.id != order_with_card_aux.id and order_with_card.order_reference == order_with_card_aux.order_reference:
                    exists_line = True
                    break
            if exists_line:
                order = self.env['pos.order'].search(
                    [('pos_reference', '=', order_with_card.order_reference), ('amount_total', '>', '0'),
                     ('sucursal_id', '=', self.env.user.sucursal_id.id)])
                monto = 0
                for statement in order.statement_ids:
                    if statement.journal_id.type == "bank":
                        monto = statement.amount
                order_with_card_aux.amount = monto  # order_with_card.amount
                order_with_card.unlink()

        ##reviso si existe el pedido en otra conciliacion
        for order_with_card in self.card_payment_ids:
            orders = self.env['conciliation.payments.card'].search(
                [('order_reference', '=', order_with_card.order_reference),
                 ('conciliation_id.sucursal_id', '=', order_with_card.conciliation_id.sucursal_id.id),
                 ('conciliation_id', '!=', order_with_card.conciliation_id.id)])

            for order in orders:
                raise UserError(
                    'El pedido ' + str(order.order_reference) + ' ya esta asignado en la conciliación ' + str(
                        order.conciliation_id.name))

        for deposit in self.bank_deposit_ids:
            if deposit.deposited_amount <= 0:
                deposit.unlink()

    # @api.multi
    def get_thousands_format(self, quantity):
        return '{0:,.2f}'.format(quantity)

    '''@api.depends('bank_deposit_ids.deposited_amount')
    def _compute_deposited_total_amount(self):
        for deposit in self.bank_deposit_ids:
            self.deposit_total += deposit.deposited_amount'''

    # reporte

    # @api.multi
    def get_current_datetime(self):
        return str(datetime.strptime(str(str(datetime.now())[0:19]), "%Y-%m-%d %H:%M:%S"))

    # @api.multi
    def get_correct_datetime(self, str_datetime):
        if str_datetime:
            field_date = str_datetime
            start = datetime.strptime(field_date, "%Y-%m-%d %H:%M:%S")
            user = self.env.get('res.users').browse(self._uid)
            tz = pytz.timezone(user.tz) if user.tz else pytz.utc
            start = pytz.utc.localize(start).astimezone(tz)
            tz_date = start.strftime("%Y-%m-%d %H:%M:%S")
            return tz_date
        return '2017-02-02 17:30:00'

    # @api.multi
    def validate_consolidation(self):
        if self.state == 'borrador' and not self.withdraw_line_ids:
            raise ValidationError('No puedes validar una conciliación sin folios asignados.')

        retirements = self.env['account.bank.statement.line'].search(
            [('sequence_cashbox_out_id', '>', '0'),
             ('x_sucursal_id', '=', self.env.user.sucursal_id.id), ('create_date', '>=', self.start_date),
             ('name', '=', 'retiro'),
             ('create_date', '<=', self.end_date)],
            order='sequence_cashbox_out_id asc')

        for retiro_hecho in retirements:
            retiro_encontrado = False
            for retiro_conciliado in self.withdraw_line_ids:
                if retiro_hecho.sequence_cashbox_out_id == retiro_conciliado.retirement_id:
                    retiro_encontrado = True
                    break
            if not retiro_encontrado:
                raise UserError('Falta agregar el retiro con el folio: ' + str(retiro_hecho.sequence_cashbox_out_id))

        self.write({'state': 'retiros_validados',
                    'validate_retirements_uid': self.env.uid,
                    'validate_retirements_date': datetime.now(),
                    'name': self.name + ' ' + str(self.start_date)[0:10]
                    })

    '''return {
        'type': 'ir.actions.report.xml',
        'report_name': 'smay_reconciliation_of_withdrawals.conciliation_retirements_bank',
        'report_type': 'pdf',
        'attachment': False,
    }'''

    # @api.multi
    def validate_bank_deposit(self):
        if self.state == 'retiros_validados' and not self.bank_deposit_ids:
            raise ValidationError('No puedes validar sin depositos bancarios asignados.')
        self.write({'state': 'deposito_validado',
                    'validate_deposits_uid': self.env.uid,
                    'validate_deposits_date': datetime.now()
                    })

    # funcoines para el reporte
    '''@api.multi
    def get_information_by_folio(self, folio):
        record = self.env['conciliation.withdrawals.line'].search([('retirement_id', '=', folio)])
        data = {}
        data['state'] = record.reconciliation_withdraw_id.state
        data['name'] = record.reconciliation_withdraw_id.name
        return data'''

    '''@api.multi  # revisar la sucursal
    def get_pending_validation_retirements(self):
        conciliations = self.env['conciliation.withdrawals'].search(
            [('state', 'in', ['borrador', 'retiros_validados'])])
        id_retirements = []
        for conciliation in conciliations:
            for retirement in conciliation.withdraw_line_ids:
                id_retirements.append(retirement.retirement_id)
        pending_retirements = self.env['account.bank.statement.line'].search(
            [('sequence_cashbox_out_id', '>', '0'), ('sequence_cashbox_out_id', 'in', id_retirements),
             ('x_sucursal_id', '=', self.env.user.sucursal_id.id)],
            order='sequence_cashbox_out_id asc')
        return pending_retirements'''

    '''@api.multi
    def get_pending_retirements(self):
        conciliations = self.env['conciliation.withdrawals'].search(
            [('state', 'in', ['borrador', 'retiros_validados', 'deposito_validado'])])
        id_retirements = []
        for conciliation in conciliations:
            for retirement in conciliation.withdraw_line_ids:
                id_retirements.append(retirement.retirement_id)
        pending_retirements = self.env['account.bank.statement.line'].search(
            [('sequence_cashbox_out_id', '>', '0'), ('sequence_cashbox_out_id', 'not in', id_retirements),
             ('x_sucursal_id', '=', self.env.user.sucursal_id.id)],
            order='sequence_cashbox_out_id asc')
        return pending_retirements'''

    '''@api.multi
    def get_sorted_retirements(self):
        if self.withdraw_line_ids:
            ids = []
            for id in self.withdraw_line_ids:
                ids.append(id.id)
            retiros = self.env['conciliation.withdrawals.line'].search([('id', 'in', ids)], order="retirement_id asc")
            return retiros
        return'''


class SmayReconciliationMissedCash(models.Model):
    _name = 'conciliation.missed.cash'
    _description = 'Registra los faltantes de los cajeros'

    reconciliation_withdraw_id = fields.Many2one('conciliation.withdrawals', 'ID retiro concentrador',
                                                 ondelete="cascade")
    cajero_id = fields.Char(string='Cajero', required=True, )
    amount = fields.Float(string="Monto del Faltante", required=True, )
    commentary = fields.Char(string='Observaciones')


class SmayReconciliationSobrantes(models.Model):
    _name = 'conciliacion.sobrante.efectivo'
    _description = 'Registra los sobrante de los cajeros'

    conciliation_id = fields.Many2one('conciliation.withdrawals', 'ID retiro concentrador',
                                      ondelete="cascade")

    cajero_id = fields.Char(string='Cajero', required=True, )
    amount = fields.Float(string="Monto del Sobrante", required=True, )
    commentary = fields.Char(string='Observaciones')


class SmayReconciliationWithdrawalsLine(models.Model):
    _name = 'conciliation.withdrawals.line'
    _description = 'almacena los retiros'

    retirement_id = fields.Integer(string='Folio del Retiro de caja', required=True, default='')
    total_amount = fields.Float(string="Monto del Retiro")
    real_amount = fields.Float(string="Monto Real", required=True)
    difference = fields.Float(string="Diferencia")
    commentary = fields.Char(string='Observaciones')
    reconciliation_withdraw_id = fields.Many2one('conciliation.withdrawals', 'ID retiro concentrador',
                                                 ondelete="cascade")

    '''
    @api.onchange('retirement_id')
    def _onchange_retirement_id(self):
        if self.retirement_id < 0:
            self.unlink()
            self.retirement_id = 0
            raise UserError("El folio del retiro no es valido.")
        if self.retirement_id > 0:

            retirement = self.env['account.bank.statement.line'].search(
                [('sequence_cashbox_out_id', '=', self.retirement_id),
                 ('x_sucursal_id', '=', self.env.user.sucursal_id.id)])
            if retirement:
                if retirement.create_date > self.reconciliation_withdraw_id.end_date or retirement.create_date < self.reconciliation_withdraw_id.start_date:
                    self.unlink()
                    raise UserError(
                        'El retiro esta fuera del rango de fechas seleccionado. El retiro fue hecho el ' + str(
                            self.reconciliation_withdraw_id.get_correct_datetime(
                                str(retirement.create_date)[0:19])))

                for line in self:
                    line.real_amount = abs(retirement.amount)
                    line.total_amount = abs(retirement.amount)
            else:
                self.unlink()
                raise ValidationError("El folio del retiro no existe.")

    # @api.onchange('real_amount')
    def _onchange_real_amount(self):
        for line in self:
            if line.real_amount != line.total_amount:
                if line.real_amount < 0:
                    line.real_amount = 0
                    raise ValidationError('El monto ingresado es incorrecto, debe ser un número positivo.')
                line.difference = line.real_amount - line.total_amount
                line.commentary = 'Describe la diferencia.'
    '''


class SmayConciliationPaymentsWithCard(models.Model):
    _name = 'conciliation.payments.card'
    _description = 'Guarda la relacion de los pagos con tarjeta'

    conciliation_id = fields.Many2one('conciliation.withdrawals', 'ID deposito de conciliacion', ondelete="cascade")
    order_reference = fields.Char(string='Referencia', required=True)
    amount = fields.Float(string='Monto con Tarjeta')
    cajero = fields.Char(string='Cajero', store=True)
    session = fields.Char(string='Sesión', store=True)
    commentary = fields.Char(string='Comentarios')
    reconciliation_withdraw_id = fields.Many2one('conciliation.withdrawals', 'ID retiro concentrador',
                                                 ondelete="cascade")

    '''
    @api.onchange('order_reference')
    def _onchage_order_reference(self):
        if self.order_reference:

            reference = str(self.order_reference).replace(' ', '-')
            reference = str(reference).replace('Pedido-', 'Pedido ')

            if 'Pedido' not in reference:
                reference = 'Pedido ' + reference

            order = self.env['pos.order'].search([('pos_reference', '=', reference), ('amount_total', '>', '0'),
                                                  ('sucursal_id', '=', self.env.user.sucursal_id.id)])
            if order:
                if order.create_date > self.conciliation_id.end_date or order.create_date < self.conciliation_id.start_date:
                    self.unlink()
                    raise UserError(
                        'El pedido esta fuera del rango de fechas seleccionado. El pedido fue hecho el ' + str(
                            self.reconciliation_withdraw_id.get_correct_datetime(
                                str(order.create_date)[0:19])))

                for line in self:
                    line.session = order.session_id.name
                    line.order_reference = reference
                    line.cajero = order.user_id.name
                for statement in order.statement_ids:
                    if statement.journal_id.type == "bank":
                        line.amount = statement.amount
                    if line.amount <= 0:
                        raise UserError('El pedido no tiene pagos con tarjeta.')
            else:
                self.order_reference = ''
                self.unlink()
                raise UserError(str(reference) + ' no se encontro. Intenta de nuevo. ')
    '''


class SmayReconciliationRefunds(models.Model):
    _name = 'conciliation.refunds'
    _description = 'Almacena las devoluciones hechas por el cajero'

    conciliation_id = fields.Many2one('conciliation.withdrawals', 'ID de conciliacion', ondelete='cascade')
    cajero_id = fields.Many2one('res.users', 'Cajero que realizó la devolución')
    motivo_devolucion = fields.Char('Motivo de la devolución')
    pos_reference = fields.Char('Pedido del POS')
    amount = fields.Float(string='Monto de la devolución')


class SmayReconciliationPrestamos(models.Model):
    _name = 'conciliation.prestamos'
    _description = 'Almacena las retiros de gastos'

    conciliation_id = fields.Many2one('conciliation.withdrawals', 'ID de conciliacion', ondelete='cascade')
    description = fields.Char('Descripcion')
    amount = fields.Float(string='Monto del prestamo')
    retirement_id = fields.Float(string='Folio de Prestamo')


class SmayReconciliationGastos(models.Model):
    _name = 'conciliation.gastos'
    _description = 'Almacena las retiros para gastos'

    conciliation_id = fields.Many2one('conciliation.withdrawals', 'ID de conciliacion', ondelete='cascade')
    description = fields.Char('Descripcion')
    amount = fields.Float(string='Monto del gasto')
    retirement_id = fields.Float(string='Folio de Gasto')


class SmayReconciliationBankDepositsLines(models.Model):
    _name = 'conciliation.bank.deposit'
    _description = 'registra los depositos bancarios'

    conciliation_id = fields.Many2one('conciliation.withdrawals', 'ID de conciliacion', ondelete="cascade")
    reference = fields.Char(string='referencia', required=True)
    deposited_amount = fields.Float(string='Monto depositado', required=True, default='')
    depositor = fields.Char(string='Persona que deposito', required=True)
    deposit_date = fields.Date(string='Fecha del Deposito', required=True, default=fields.Date.context_today)
    deposito_validado_en_banco = fields.Float(string='Monto Verificado en Banco', default=0)

    bank = fields.Selection(selection=[
        ('BANAMEX', 'Banamex'),
        ('BANCOMER', 'Bancomer'),
        ('BANORTE', 'Banorte'),
        ('SCOTIABANK', 'Scotiabank'),
        ('SANTANDER', 'Santander'),
        ('HSBC', 'HSBC'),
        ('BANREGIO', 'Banregio'),
    ], string='Banco', required=True, default='')

    @api.onchange('deposited_amount')
    def _check_fields(self):
        for record in self:
            if record.deposited_amount <= 0 and record.bank:
                raise ValidationError('El monto depositado debe de ser mayor a 0.')

    '''@api.onchange('deposito_validado_en_banco')
    def _onchange_deposito_validado(self):
        self.conciliation_id.total_conciliado_banco = 1000'''
