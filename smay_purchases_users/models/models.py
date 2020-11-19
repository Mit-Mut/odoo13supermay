# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
import base64
import pytz

_logger = logging.getLogger(__name__)
from odoo.addons.purchase.models.purchase import PurchaseOrder as Purchase


class SmayPurchasesUsersResUsers(models.Model):
    _inherit = 'res.users'

    x_almacen_compras = fields.Many2one('stock.picking.type', string='Almacen de sucursal para compras',
                                        domain="[('code','=','incoming')]")
    x_cuenta_analitica = fields.Many2one('account.analytic.account', string='Cuenta Analitica',
                                         help='Asigna la cuenta analitica a las compras.')

    purchase_validator = fields.Boolean('Puede validar compras.', default=False)


class SmayPurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                          default=lambda self: self._default_account_analytic())

    @api.model
    def _default_account_analytic(self):
        if self.env.user.has_group('purchase.group_purchase_manager'):
            return
        else:
            return self.env.user.x_cuenta_analitica.id


class SmayPurchasesOrder(models.Model):
    _inherit = 'purchase.order'

    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', states=Purchase.READONLY_STATES,
                                      required=True, default=lambda self: self._default_picking_type(),
                                      help="This will determine operation type of incoming shipment")

    analytic_account_select = fields.Many2one('account.analytic.account', string='Cuenta Analitica')

    # cantidad_lineas = fields.Integer('Items', default=0)
    cantidad_lineas = fields.Integer('Items', compute='_compute_qty_lines')

    # cantidad_productos = fields.Float('Cantidad Prods.', default=0)
    cantidad_productos = fields.Float('Cantidad Prods.', compute='_compute_qty_products')

    def _compute_qty_products(self):
        self.cantidad_productos = 0
        for line in self.order_line:
            self.cantidad_productos += line.product_qty

    def _compute_qty_lines(self):
        self.cantidad_lineas = len(self.order_line)

    @api.onchange('analytic_account_select')
    def on_change_analytic_account(self):
        for line in self.order_line:
            line.write({
                'account_analytic_id': self.analytic_account_select.id
            })

    @api.onchange('order_line')
    def _onchange_line(self):
        self.cantidad_lineas = len(self.order_line)
        self.cantidad_productos = 0
        for line in self.order_line:
            line.analytic_account_select = self.analytic_account_select.id
            self.cantidad_productos += line.product_qty

    def write(self, vals):
        self.validate_purchase(vals)
        record = super(SmayPurchasesOrder, self).write(vals)
        self.validate_purchase_records()
        return record

    def validate_purchase_records(self):
        i = 0

        if self.id and len(self.browse(self.id).order_line) == 0:
            raise UserError('La compra debe de contener productos agregados')
        for line in self.order_line:
            if line.price_unit <= 0:
                raise UserError('El precio del producto ' + str(self.product_id.name) + ' debe ser mayor a 0.')
            if line.product_qty <= 0:
                raise UserError('La cantidad del producto ' + str(self.product_id.name) + ' debe ser mayor a 0.')
            j = 0
            for line2 in self.order_line:
                if i != j and line.product_id.id == line2.product_id.id:
                    raise UserError('El product ' + str(line.product_id.name) + ' esta repetido')
                j = j + 1
            i = i + 1

    def validate_purchase(self, vals):
        if vals.get('order_line'):
            i = 0
            for line in vals.get('order_line'):
                if line[0] == 0:
                    linea = line[2]
                    if linea.get('price_unit') <= 0:
                        raise UserError('El precio del producto ' + str(
                            self.env['product.product'].browse(linea.get('product_id')).name) + ' debe ser mayor a  0.')
                    if linea.get('product_qty') <= 0:
                        raise UserError('la cantidad del producto ' + str(
                            self.env['product.product'].browse(linea.get('product_id')).name) + ' debe ser mayor a 0.')

                    # revisa si se repiten
                    j = 0
                    for line2 in vals.get('order_line'):

                        if line2[0] == 0:
                            linea2 = line2[2]
                            if j != i and linea.get('product_id') == linea2.get('product_id'):
                                raise UserError('El producto ' + str(self.env['product.product'].browse(
                                    linea.get('product_id')).name) + ' esta repetido.')
                            j = j + 1
                    i = i + 1

    @api.model
    def create(self, vals):

        self.validate_purchase(vals)
        record = super(SmayPurchasesOrder, self).create(vals)
        self.validate_purchase_records()
        return record

    @api.model
    def _default_picking_type(self):
        if self.env.user.has_group('purchase.group_purchase_manager'):
            return
        else:
            return self.env.user.x_almacen_compras.id

    def button_confirm(self):
        for line in self.order_line:
            if not line.account_analytic_id:
                raise UserError('No tiene asignada la cuenta analitica en ' + str(self.product_id.name))
        if self.env.user.has_group('purchase.group_purchase_manager'):
            super(SmayPurchasesOrder, self).button_confirm()
            self.update_information_product()
            # self.button_done()
            return
        else:
            if not self.env.user.purchase_validator:
                raise UserError('No tienes los privilegios para validar compras.')
            if self.create_uid == self.env.user.id:
                raise UserError('No puedes confirmar la orden de compra de esta sucursal.')

            if self.picking_type_id.id == self.env.user.x_almacen_compras.id:
                super(SmayPurchasesOrder, self).button_confirm()
                self.update_information_product()
                # self.button_done()
                return
            else:
                raise UserError('No puedes confirmar compras de otro almacen (Sucursal).')

    '''test'''

    # def action_view_picking(self):
    def update_information_product(self):
        # resulta = super(SmayPurchasesOrder, self).action_view_picking()
        if True:
            '''for line in self.env['stock.picking'].browse(resulta.get('res_id')).move_ids_without_package:
                for _line in line.move_line_ids:
                    _line.sudo(True).write({
                        'qty_done': _line.product_uom_qty,
                    })

            pickings = self.env['stock.picking'].browse(resulta.get('res_id'))
            for picking in pickings:
                picking.button_validate()'''

            products = []
            diferencial_cambio_precio = .20
            for line in self.order_line:
                _product = {}
                if line.product_id.standard_price < line.price_unit:
                    if round(((line.product_id.x_utility_percent / 100) + 1) * line.price_unit,
                             1) > line.product_id.list_price:

                        if round(line.price_unit - line.product_id.standard_price, 1) >= diferencial_cambio_precio:
                            products.append(line.product_id.id)
                            _product['id'] = line.product_id.id
                            _product['old_cost'] = line.product_id.standard_price
                            _product['new_cost'] = line.price_unit
                            _product['old_list_price'] = line.product_id.list_price
                            _product['new_list_price'] = round(
                                ((line.product_id.x_utility_percent / 100) + 1) * line.price_unit, 1)

                            line.product_id.sudo(True).write({
                                'standard_price': _product['new_cost'],
                                'list_price': _product['new_list_price'],
                                'x_purcharse_change_price': self.name,
                            })

                            line.product_id.product_tmpl_id.sudo(True).write({
                                'x_fecha_actualizacion_precios': line.write_date,
                                'x_sent_labels': False,
                                'x_last_price': _product['old_list_price']
                            })



                        else:
                            line.product_id.sudo(True).write({
                                'standard_price': line.price_unit,
                                # 'list_price': ((line.product_id.x_utility_percent / 100) + 1) * line.price_unit,
                                # 'x_purcharse_change_price': self.name,
                            })
                    elif round(((line.product_id.x_utility_percent / 100) + 1),
                               1) * line.price_unit < line.product_id.list_price:
                        line.product_id.sudo(True).write({
                            'standard_price': line.price_unit,
                            # 'list_price': ((line.product_id.x_utility_percent / 100) + 1) * line.price_unit,
                            # 'x_purcharse_change_price': self.name,
                        })

                ###CAMBIO DE COMPRAS 20200627
                elif line.product_id.standard_price > line.price_unit:
                    line.product_id.sudo(True).write({
                        'standard_price': line.price_unit
                    })
                prd_tmpl = line.product_id.product_tmpl_id
                for provider in line.product_id.seller_ids:
                    _logger.warning(str(provider.product_tmpl_id.id))
                    _logger.warning(str(prd_tmpl.id))
                    _logger.warning(str(provider.name.id))
                    _logger.warning(str(self.partner_id.id))
                    if provider.product_tmpl_id.id == prd_tmpl.id and provider.name.id == self.partner_id.id:
                        provider.sudo(True).write({
                                'price': line.price_unit
                        })

        return True

    '''def print_labels(self):
        self.ensure_one()
        products = []
        for line in self.order_line:
            products.append(line.product_id.id)
        products = self.env['product.product'].search([('x_purcharse_change_price', '=', self.name)])
        if products:
            return self.env.ref('product.report_product_label').report_action(products)
        raise UserError('No hubo cambios de precios.')'''

    ##esta funcion se manda llamar desde la tarea programada
    def send_changed_labels(self):
        product_tmpls = self.env['product.template'].search([('x_sent_labels', '=', False)])

        tmpl_ids = []
        for product_tmpl in product_tmpls:
            tmpl_ids.append(product_tmpl.id)

        if tmpl_ids:
            products = self.env['product.product'].search([('product_tmpl_id', 'in', tmpl_ids)])

            prods = []
            for product in products:
                prods.append(product.id)

            # send mail
            email_to = ''
            for user in self.env.user.company_id.x_notification_partner_ids:
                if user.email:
                    email_to += user.email + ';'

            if email_to == '':
                _logger.warning('No hay usuarios configurados en la compañia para enviar las etiquetas')
                return

            mail = self.env['mail.mail']
            data = {}
            data['subject'] = 'Cambios de Costos y Precios'
            data['email_to'] = email_to
            data['body_html'] = 'Buen día,<br/><br/>'
            data[
                'body_html'] += 'Los costos y precios de los siguientes productos fueron modificados en el proceso de compra:<br/><br/>'

            data['body_html'] += "<table style='border:2px solid black' cellpadding='0' cellspacing='0' width='80%' align='center'>\
                            <tr style='background-color:#BA3B20;color:#FFFFFF'>\
                                <th style='border:1px solid white' width='40%'>PRODUCTO</th>\
                                <th style='border:1px solid white' width='15%'>COMPRA</th>\
                                <th style='border:1px solid white' width='15%'>FECHA</th>\
                                <th style='border:1px solid white' width='15%'>PRECIO ANTERIOR</th>\
                                <th style='border:1px solid white' width='15%'>PRECIO ACTUAL</th>\
                            </tr>"

            # for product in products:
            for product in products:
                fecha = ''
                if product.product_tmpl_id.x_fecha_actualizacion_precios:
                    fecha = product.product_tmpl_id.x_fecha_actualizacion_precios
                    local = pytz.timezone(str(self.env.get('res.users').browse(self._uid).tz))
                    fecha_usuario = fecha.astimezone(tz=local).strftime('%Y-%m-%d %H:%M:%S')
                if not fecha_usuario:
                    fecha_usuario = ''
                data['body_html'] += "<tr>\
                    <td style='border:1px solid white;border-bottom:1px solid black;border-right:1px solid black;padding-left:5px'>" + product.product_tmpl_id.name + "</td>\
                    <td style='border:1px solid white;border-bottom:1px solid black;border-right:1px solid black;padding-left:5px'>" + product.x_purcharse_change_price + "</td>\
                    <td style='border:1px solid white;border-bottom:1px solid black;border-right:1px solid black;padding-left:5px'>" + fecha_usuario + "</td>\
                    <td style='border:1px solid white;border-bottom:1px solid black;border-right:1px solid black;text-align:right;padding-right:5px'> $" + '{:,.2f}'.format(
                    product.product_tmpl_id.x_last_price) + "</td>\
                    <td style='border:1px solid white;border-bottom:1px solid black;text-align:right;padding-right:5px'><b> $" + '{:,.2f}'.format(
                    product.list_price) + "</b></td></tr>"

                prd_tmpl= product.product_tmpl_id
                prd_tmpl.sudo(True).write({
                    'x_sent_labels': True
                }
                )



            data['body_html'] += '</table>'
            data[
                'body_html'] += '<br/><br/>Se adjunta el archivo con los nuevos precios para reemplazarlo en piso de venta.'
            data['body_html'] += '<br/><br/>'
            data['body_html'] += 'S@lu2.'

            msg = mail.create(data)
            prices = self.env.ref('product.report_product_label').render_qweb_pdf(prods)
            b64_pdf = base64.b64encode(prices[0])

            msg.update({
                'attachment_ids': [(0, 0, {
                    # 'name': 'Etiquetas - Cambios de precio',
                    'type': 'binary',
                    'datas': b64_pdf,
                    'name': 'Etiquetas - Cambios de precio.pdf',
                    'store_fname': 'Etiquetas - Cambios de precio',
                    'res_model': self._name,
                    'res_id': self.id,
                    'mimetype': 'application/x-pdf'
                })]
            })
            if msg:
                mail.sudo().send(msg)
                mail.sudo().process_email_queue()
        else:
            _logger.warning('No hay cambios de precios en productos')


class SmayPurchasesProduct(models.Model):
    _inherit = 'product.template'

    x_utility_percent = fields.Float(string='Porcentaje de utilidad', default=16)
    x_fecha_actualizacion_precios = fields.Datetime('Fecha en que se cambio el precio')
    x_sent_labels = fields.Boolean(defult=True)
    x_last_price = fields.Float(default=0.0, string='Precio anterior', readonly=True)


class SmayPurchasesProductProduct(models.Model):
    _inherit = 'product.product'

    x_purcharse_change_price = fields.Char(string='cambio de precio', default='')


class SmayPurchaseResCompany(models.Model):
    _inherit = 'res.company'

    x_notification_partner_ids = fields.Many2many('res.partner', string='Usuarios notificados en compras')
