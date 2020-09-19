# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date, time, timedelta
import logging, time

_logger = logging.getLogger(__name__)


class SmayRefundPosConfig(models.Model):
    _inherit = 'pos.config'

    x_dias_permitidos_devolucion = fields.Integer(string='Dias permitidos para la devolucion', default=8)


class smayAccountMoveReversal(models.Model):
    _inherit = 'account.move'

    def _reverse_movesSmay(self, order_to_refund,move_id, default_values_list=None, cancel=False):
        move = self.env['pos.order'].browse(move_id).account_move
        _logger.warning('GGGGGGGGGGGGGGGGGGGGGGGGGGG')
        _logger.warning(move)
        '''if not default_values_list:
            default_values_list = [{} for move in self]

        if cancel:
            lines = self.mapped('line_ids')
            # Avoid maximum recursion depth.
            if lines:
                lines.remove_move_reconcile()

        reverse_type_map = {
            'entry': 'entry',
            'out_invoice': 'out_refund',
            'out_refund': 'entry',
            'in_invoice': 'in_refund',
            'in_refund': 'entry',
            'out_receipt': 'entry',
            'in_receipt': 'entry',
        }

        move_vals_list = []
        for move, default_values in zip(self, default_values_list):
            default_values.update({
                'type': reverse_type_map[move.type],
                'reversed_entry_id': move.id,
            })'''

        move_vals_list = []

        move_vals_list.append(move._reverse_move_vals(default_values_list, cancel=cancel))

        _logger.warning('SALIDA CON ARREGLO')
        _logger.warning(str(move_vals_list))


        '''reverse_moves = self.env['account.move'].create(move_vals_list)

        # I modify credits and debits for I can delete records

        # I get ID of totals
        line_totals_id = 0
        tax_line_ids = {}
        product_line_ids = {}
        for line in reverse_moves.line_ids:
            if not line.product_id and not line.tax_line_id:
                line_totals_id = line.id
                continue
            if not line.product_id and line.tax_line_id:
                tax_line_ids[line.name] = line.id
                continue
            if line.product_id:
                product_line_ids[line.product_id.id] = line.id
                continue'''

        # I obtain the ID of taxes
        '''tax_line_ids = {}
        for line in reverse_moves.line_ids:
            if not line.product_id and line.tax_line_id:
                tax_line_ids[line.name] = line.id

        # I obtain the ID of products
        product_line_ids = {}
        for line in reverse_moves.line_ids:
            if line.product_id:
                product_line_ids[line.product_id.id] = line.id'''

        '''refund_order = self.env['pos.order'].browse(order_to_refund)

        _logger.warning('LOS IDASSSS A TRABAJAR')
        _logger.warning('TACES' + str(tax_line_ids))
        _logger.warning('TOTAL' + str(line_totals_id))
        _logger.warning('PRODUCTOS' + str(product_line_ids))

        ######################################
        # I  verify if the credit note is partial o full
        if refund_order.amount_total != reverse_moves.amount_total_signed:
            # I set to 0 some fields of records oof tax
            for imp in tax_line_ids.keys():
                tax_line_id = tax_line_ids[imp]
                self._cr.execute("""UPDATE account_move_line 
                                    SET ref=ref ,
                                        debit=0.00,                                        
                                        price_subtotal=0.00,
                                        price_total=0.00,
                                        tax_base_amount=0.00,
                                        balance=0.00
                                    WHERE id=%d""" % (tax_line_id))

            # Recorro las lineas de factura para revisar cuales ajustar para porder eliminarlas
            for vent in product_line_ids.keys():
                self._cr.execute("""UPDATE account_move_line 
                                    SET quantity=0.00,
                                        debit = 0.00, 
                                        credit=0.00, 
                                        balance=0.00
                                    WHERE id=%d""" % (product_line_ids[vent]))
            _lineas_borrar = []
            for order_line in refund_order.lines:
                # Comparo con la orden de devolucion
                for invoice_line in reverse_moves.line_ids:
                    # esta en la orden de devolucion
                    if invoice_line.product_id and order_line.product_id.id == invoice_line.product_id.id:
                        self._cr.execute("""UPDATE account_move_line 
                                            SET quantity = %f, 
                                                debit=%f, 
                                                credit=0.00,
                                                balance=0.00,
                                                price_subtotal=%f,
                                                price_total=%f
                                            WHERE id =%d""" % (abs(order_line.qty),
                                                               abs((order_line.price_subtotal) / abs(order_line.qty)),
                                                               # abs(order_line.price_subtotal),
                                                               abs(order_line.price_subtotal),
                                                               abs(order_line.price_subtotal_incl),
                                                               invoice_line.id))

            # recalculo los taxes despues de dejar a punto los productos
            for invoice_line in reverse_moves.line_ids:
                self._cr.execute("""SELECT debit,
                                            credit,
                                            price_total, 
                                            price_subtotal 
                                    FROM account_move_line 
                                    WHERE id =%d""" % (invoice_line.id))

                resultado = self._cr.dictfetchone()
                _debit = resultado['debit']
                _credit = resultado['credit']
                _price_subtotal = resultado['price_subtotal']
                _price_total = resultado['price_total']

                # analizo si la linea de producto tiene impuestos para sumarlos
                if (invoice_line.product_id and _debit > 0) and (_price_subtotal != _price_total):

                    self._cr.execute("""SELECT debit 
                                        FROM account_move_line 
                                        WHERE id =%d""" % (tax_line_id))
                    _tax_debit = self._cr.dictfetchone()['debit']

                    tag_tax = ''
                    for tax in invoice_line.product_id.taxes_id:
                        tag_tax = tax.name

                    if tag_tax != '':
                        line_tax = self.env['account.move.line'].browse(tax_line_ids[tag_tax])
                        nuevo_monto = round(_tax_debit + (_price_total - _price_subtotal), 2)

                        self._cr.execute("""UPDATE account_move_line 
                                            SET debit = %f, 
                                                credit=0.00, 
                                                balance=%f,
                                                price_unit=%f,
                                                price_subtotal=%f
                                            WHERE id=%d""" % (nuevo_monto,
                                                              nuevo_monto,
                                                              nuevo_monto,
                                                              nuevo_monto,
                                                              line_tax.id))

            ##sumo los debit de todos los lines y los pongo en la linea de totales

            self._cr.execute("""SELECT sum(debit) as debit 
                                FROM account_move_line 
                                WHERE move_id = %d 
                                AND id <> %d""" % (reverse_moves.id, line_totals_id))

            _credit = self._cr.dictfetchone()['debit']

            self._cr.execute("""UPDATE account_move_line
                                SET credit = %f,
                                    balance = %f,
                                    price_unit = %f,
                                    price_total = %f,
                                    price_subtotal=%f,
                                    amount_residual =%f
                                WHERE id = %d""" % (_credit,
                                                    -_credit,
                                                    -_credit,
                                                    -_credit,
                                                    -_credit,
                                                    -_credit,
                                                    line_totals_id))
        else:
            _logger.warning('Se hizo un nota de credito total de la factura.')

        for move, reverse_move in zip(self, reverse_moves.with_context(check_move_validity=False)):
            # Update amount_currency if the date has changed.
            if move.date != reverse_move.date:
                for line in reverse_move.line_ids:
                    if line.currency_id:
                        line._onchange_currency()
            reverse_move._recompute_dynamic_lines(recompute_all_taxes=False)
        reverse_moves._check_balanced()

        # Reconcile moves together to cancel the previous one.
        if cancel:
            reverse_moves.with_context(move_reverse_cancel=cancel).post()
            for move, reverse_move in zip(self, reverse_moves):
                accounts = move.mapped('line_ids.account_id') \
                    .filtered(lambda account: account.reconcile or account.internal_type == 'liquidity')
                for account in accounts:
                    (move.line_ids + reverse_move.line_ids) \
                        .filtered(lambda line: line.account_id == account and line.balance) \
                        .reconcile()

        return reverse_moves'''


class SmayRefundPosOrder(models.Model):
    _inherit = 'pos.order'

    is_refund = fields.Boolean(string='Es devolucion', default=False)
    x_motivo_devolucion = fields.Char(string='Motivo de la devolucion', readonly=True)
    x_descripcion_devolucion = fields.Char(string='Descripcion del motivo de la devolucion', readonly=True)

    @api.model
    def get_information_reprint(self, order_id, recalculo_pzs):
        order = self.browse(int(order_id))
        data = super(SmayRefundPosOrder, self).get_information_reprint(order_id, recalculo_pzs)
        data['x_motivo_devolucion'] = order.x_motivo_devolucion if order.x_motivo_devolucion else ''
        data['x_descripcion_devolucion'] = order.x_descripcion_devolucion if order.x_motivo_devolucion else ''

        if order.amount_total > 0 and recalculo_pzs:
            refund_orders = self.env['pos.order'].search(
                [('pos_reference', '=', order.pos_reference), ('amount_total', '<', 0)])
            for refund_order in refund_orders:
                for refund_line in refund_order.lines:
                    for orderline in data.get('orderlines'):
                        if refund_line.product_id.id == int(orderline['product_id']):
                            orderline['qty'] += refund_line.qty
                            continue
            return data
        if order.amount_total < 0 and recalculo_pzs == False:
            original_order = self.env['pos.order'].search(
                [('pos_reference', '=', order.pos_reference), ('amount_total', '>', 0)])
            for order_line in order.lines:
                for order_line_orig in original_order.lines:
                    if order_line.product_id.id == order_line_orig.product_id.id:
                        order_line.write({
                            'x_descuento': (order_line_orig.x_descuento / order_line_orig.qty) * order_line.qty,
                        })
                        continue

            for order_line in data.get('orderlines'):
                for order_line_orig in original_order.lines:
                    if order_line['product_id'] == order_line_orig.product_id.id:
                        order_line['descuento_smay'] = (order_line_orig.x_descuento / order_line_orig.qty) * order_line[
                            'qty']
                    continue
            return data

        return data

    @api.model
    def exist_order(self, pos_reference):
        today = datetime.now().replace(microsecond=0)
        current_sesion = self.env['pos.session'].search([('user_id', '=', self._uid), ('state', '=', 'opened')],
                                                        order='id desc', limit=1)
        allowed_date = today - timedelta(days=current_sesion.config_id.x_dias_permitidos_devolucion)
        '''order = self.search(
            [('id', '>', '0'), ('pos_reference', 'like', pos_reference)])  # , ('date_order', '<=', str(allowed_date))])'''

        config_ids = []
        for config_id in self.env.user.pos_config_ids:
            config_ids.append(config_id.id)

        order = self.search([('pos_reference', 'like', pos_reference), ('config_id', 'in', config_ids),
                             ('date_order', '<', str(allowed_date))], limit=1)
        if order:
            return -3
        order = self.search(
            [('pos_reference', 'like', pos_reference), ('config_id', 'in', config_ids), ('amount_total', '>', '0')],
            # ('is_refund', '=', False)],
            limit=1, order="id asc")

        if order:
            # if order.is_refund or order.amount_total <= 0:
            if order.amount_total <= 0:
                return -1  # exist a refund for this order
            '''if order.date_order >= allowed_date:
                return -3'''

            return order.id  # the order is correct

        return -2  # don't exist the order that user input

    # @api.model
    def _order_has_invoice(self, order_id):
        order = self.env['pos.order'].browse(order_id)
        if order.account_move:
            return order.id
        return -1

    # se hizo esta funcion para la nota de credito pero no funciono, esta pendiente
    @api.model
    def limpia_factura(self, order_id):
        # return True
        nota_credito = self.env['pos.order'].browse(order_id).account_move

        for line in nota_credito.line_ids:
            if line.quantity == 0 and (line.product_id):
                line.unlink()
                continue

            line.write({
                'balance': line.debit - line.credit,
            })
        # nota_credito._compute_amount()
        # nota_credito.action_post()
        return True

    @api.model
    def get_data_order(self, pos_reference, order_to_refund):
        _logger.warning('DEVOLUCIONAAAAAAAAA')
        _logger.warning(str(order_to_refund))
        order = self.search(
            [('pos_reference', '=', pos_reference),  # ('is_refund', '=', False),
             ('amount_total', '>', '0')], limit=1, order="id asc")

        if order:
            total = 0
            current_session = self.env['pos.session'].search(
                [('state', '=', 'opened'), ('user_id', '=', self.env.user.id)])
            for orderline in order_to_refund:
                if orderline.get('cantidad') == 0:
                    continue
                total += float(orderline.get('cantidad')) * float(orderline.get('precio_unitario').replace('$', ''))

            if total > current_session.cash_register_total_entry_encoding:
                return -2

            refund_order_id = order.pos_refund(order_to_refund)

            if order.account_move:
                invoice_order = self.env['account.move'].browse(order.account_move.id)
                refund_order = self.env['pos.order'].browse(refund_order_id)

                ref = {
                    'journal_id': invoice_order.journal_id.id,
                    'ref': ('Nota de Credito: %s') % (invoice_order.name),
                    'type': 'out_refund',
                    'reversed_entry_id': invoice_order.id,
                }

                #GENERA LA DEVOLUCION Y REGRESA EL REGISTRO
                factura_devolucion = invoice_order._reverse_movesSmay(refund_order_id,invoice_order.id, [ref], cancel=False, )




                for invoice_line in factura_devolucion.invoice_line_ids:
                    _logger.warning('LINEA DE FACTURA')
                    _logger.warning(str(invoice_line.quantity))
                    # invoice_line.unlink()

                refund_order.write({
                    'account_move': factura_devolucion.id,
                    'state': 'invoiced',
                })
    
                reverse._affect_tax_report()
                reverse.action_post()
                
    
                
                refund_invoice_order.action_invoice_open()
                # time.sleep(3)
                email_act = refund_invoice_order.action_invoice_sent()
                if email_act and email_act.get('context'):
                    email_ctx = email_act['context']
                    email_ctx.update(default_email_from=refund_invoice_order.company_id.email)
                    refund_invoice_order.message_post_with_template(email_ctx.get('default_template_id'))

            return refund_order_id
        return -1

    # @api.multi
    def pos_refund(self, order_to_refund):
        """Create a copy of order  for refund order"""
        refund_order_data = self.refund()
        refund_order = self.search([('id', '=', refund_order_data['res_id'])])
        refund_order.write({
            'partner_id': self.partner_id.id,
            'is_refund': True
        })

        self.write({
            'is_refund': True
        })

        i = 0
        for orderline in refund_order.lines:
            orderline.sudo().write({
                'qty': - int(order_to_refund[i].get('cantidad')),
                'price_unit': float(order_to_refund[i].get('precio_unitario').replace('$', '')),
                'price_subtotal': int(order_to_refund[i].get('cantidad')) * float(
                    order_to_refund[i].get('precio_unitario').replace('$', '')),

            })

            orderline._onchange_qty()
            i += 1

        for line in refund_order.lines:
            if line.qty == 0:
                line.unlink()

        refund_order._onchange_amount_all()

        if len(refund_order.lines) >= 1:
            refund_order.write({
                'x_motivo_devolucion': order_to_refund[0].get('motivo'),
                'x_descripcion_devolucion': order_to_refund[0].get('descripcion_devolucion'),

            })

        # select automatically the payment
        data = dict()
        data['create_uid'] = (self.env.user.id, self.env.user.name)
        data['pos_order_id'] = refund_order.id

        current_session = self.env['pos.session'].search([('state', '=', 'opened'), ('user_id', '=', self.env.user.id)])
        # for journal in current_session.config_id.journal_ids:
        for method in current_session.config_id.payment_method_ids:
            if method.is_cash_count:
                data['payment_method_id'] = method.id

        data['session_id'] = current_session.id

        data['write_uid'] = data['create_uid']
        data['amount'] = refund_order.amount_total

        refund_order.add_payment(data)
        refund_order.action_pos_order_paid()

        return refund_order.id
