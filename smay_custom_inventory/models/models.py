# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_utils, float_compare
import logging

_logger = logging.getLogger(__name__)


class smayCustomInventoryResUser(models.Model):
    _inherit = 'res.users'

    inventory_stock_location_id = fields.Many2one('stock.location', string='Almacen para realizar inventarios.',
                                                  domain="[('name','=','Stock')]")

    inventory_validator = fields.Boolean(string='Puede validar inventarios.')


class smayTransferencesStockMove(models.Model):
    _inherit = 'stock.move'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for move in self:
            if move.product_id:
                if self.env.user.has_group('stock.group_stock_user'):
                    '''stocks = self.env['stock.quant'].search([('company_id', '=', self.env.user.company_id.id),
                                                             ('location_id', '=', self.location_id.id),
                                                             ('product_id', '=', move.product_id.id)]).quantity
                    reserved = self.env['stock.quant'].search([('company_id', '=', self.env.user.company_id.id),
                                                               ('location_id', '=', self.location_id.id),
                                                               ('product_id', '=', move.product_id.id)]).reserved'''
                    product = self.env['stock.quant'].search([('company_id', '=', self.env.user.company_id.id),
                                                              ('location_id', '=', self.location_id.id),
                                                              ('product_id', '=', move.product_id.id)])
                    move.product_uom_qty = product.quantity - product.reserved_quantity


class smayCustomInventoryStockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    x_diferencia_cantidad = fields.Float('Dif. Cantidad', default=0)
    x_diferencia_porcentaje = fields.Float('Dif. %', default=0)
    x_diferencia_costo = fields.Float('Dif. Costo', default=0)
    x_diferencia_venta = fields.Float('Dif. Venta', default=0)

    @api.onchange('product_id', 'product_qty', 'theoretical_qty')
    def _onchange_inventory_line(self):
        self.x_diferencia_cantidad = self.product_qty - self.theoretical_qty
        '''if self.product_qty < 0:
            raise UserError('No puedes ingresar numeros negativos')'''

        if self.theoretical_qty > 0:
            self.x_diferencia_porcentaje = round((self.x_diferencia_cantidad * 100) / self.theoretical_qty, 2)
        else:
            self.x_diferencia_porcentaje = 100
        self.x_diferencia_costo = self.x_diferencia_cantidad * self.env['product.template'].browse(
            self.product_id.product_tmpl_id.id).standard_price
        self.x_diferencia_venta = self.x_diferencia_cantidad * self.env['product.template'].browse(
            self.product_id.product_tmpl_id.id).list_price

    def _check_no_duplicate_line(self):
        return
        for line in self:
            existings = self.search([
                ('id', '!=', line.id),
                ('product_id', '=', line.product_id.id),
                ('inventory_id.state', '=', 'confirm'),
                ('location_id', '=', line.location_id.id),
                ('partner_id', '=', line.partner_id.id),
                ('package_id', '=', line.package_id.id),
                ('prod_lot_id', '=', line.prod_lot_id.id)])
            if existings:
                raise UserError(
                    _("No puede tener dos ajustes de inventario en estado 'en curso' con el mismo producto (%s),"
                      " misma ubicación, mismo paquete, mismo propietario y el mismo lote."
                      " Primero valide el primer ajuste de inventario con este producto antes de crear otro.  El ajuste en donde esta el producto es %s") % (
                        line.product_id.display_name, line.inventory_id.name))


class smayCustomInventoryStockInventory(models.Model):
    _inherit = 'stock.inventory'

    inventory_parent_id = fields.Many2one('stock.inventory', string='Inventario Padre',
                                          domain="[('state','=','confirm')]")

    location_id = fields.Many2one(
        'stock.location', 'Inventoried Location',
        readonly=True, required=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: self._default_location_id())

    def genera_segundo_conteo(self):
        for inv in self:
            vals = {'filter': 'partial',
                    'company_id': self.env.user.company_id.id,
                    'name': 'Conteo de diferencias',
                    'accounting_date': False,
                    'product_id': False,
                    'category_id': False,
                    'lot_id': False,
                    'partner_id': False,
                    'package_id': False,
                    'exhausted': True,
                    'inventory_parent_id': self.inventory_parent_id.id
                    }
            new_inv = inv.create(vals)
            new_inv.action_start()
            for line in inv.line_ids:
                if line.product_qty != line.theoretical_qty:
                    vals = {
                        'product_id': line.product_id.id,
                        'product_qty': 0,
                        'location_id': line.location_id.id,
                        'product_lot_id': False,
                        'package_id': False,
                        'partner_id': False,
                        'x_diferencia_cantidad': 0,
                        'x_diferencia_porcentaje': 0,
                        'x_diferencia_costo': 0,
                        'x_diferencia_venta': 0,
                        'product_uom_id': line.product_uom_id.id,
                        'inventory_id': new_inv.id
                    }
                    self.env['stock.inventory.line'].create(vals)
                    line.unlink()
            if len(new_inv.line_ids) == 0:
                raise UserError('El inventario no tiene productos con diferencias para generar un nuevo conteo.')

    def action_reset_product_qty(self):
        super(smayCustomInventoryStockInventory, self).action_reset_product_qty()
        for line in self.line_ids:
            line._onchange_inventory_line()

    def action_validate(self):
        '''if self.inventory_parent_id:
            if self.inventory_parent_id.id == self.id:
                raise UserError('El inventario padre no puede ser el inventario mismo.')
        parents = self.search([('inventory_parent_id', '=', False), ('state', '=', 'confirm')])
        if len(parents) > 1:
            raise UserError('Solo puede existir un inventario padre por validar, revisa los inventarios en proceso.')'''

        # raise UserError(str(parents))
        self.join_repeated_products()

        for line in self.line_ids:
            # raise UserError(str(line.id))
            existings = self.env['stock.inventory.line'].search([
                ('id', '!=', line.id),
                ('product_id', '=', line.product_id.id),
                ('inventory_id.state', '=', 'confirm'),
                ('location_id', '=', line.location_id.id),
                ('partner_id', '=', line.partner_id.id),
                ('package_id', '=', line.package_id.id),
                ('prod_lot_id', '=', line.prod_lot_id.id), ])
            if existings:
                raise UserError(
                    _("No puede tener dos ajustes de inventario en estado 'en curso' con el mismo producto (%s),"
                      " misma ubicación, mismo paquete, mismo propietario y el mismo lote."
                      " Primero valide el primer ajuste de inventario con este producto antes de crear otro.  El ajuste en donde esta el producto es %s") % (
                        line.product_id.display_name, existings[0].inventory_id.name))

        return super(smayCustomInventoryStockInventory, self).action_validate()

    def join_repeated_products(self):
        if self.inventory_parent_id:
            if self.inventory_parent_id.id == self.id:
                raise UserError('El inventario padre no puede ser el inventario mismo.   ')
        existings = []
        for line in self.line_ids:
            existings = self.env['stock.inventory.line'].search([
                ('id', '!=', line.id),
                ('product_id', '=', line.product_id.id),
                ('inventory_id.state', '=', 'confirm'),
                ('location_id', '=', line.location_id.id),
                ('partner_id', '=', line.partner_id.id),
                ('package_id', '=', line.package_id.id),
                ('inventory_id', '=', line.inventory_id.id),
                ('prod_lot_id', '=', line.prod_lot_id.id)])
            for line_aux in existings:

                if line.theoretical_qty > 0:
                    diff_percent = round((((line.product_qty + line_aux.product_qty) - line_aux.theoretical_qty) * 100)
                                         / line.theoretical_qty, 2)
                else:
                    diff_percent = 100
                diff_cost = ((line.product_qty + line_aux.product_qty) - line_aux.theoretical_qty) * self.env[
                    'product.template'].browse(
                    line.product_id.product_tmpl_id.id).standard_price
                price_sale_diff = ((line.product_qty + line_aux.product_qty) - line_aux.theoretical_qty) * self.env[
                    'product.template'].browse(
                    line.product_id.product_tmpl_id.id).list_price

                line_aux.write({
                    'product_qty': line.product_qty + line_aux.product_qty,
                    'x_diferencia_cantidad': (line.product_qty + line_aux.product_qty) - line_aux.theoretical_qty,
                    'x_diferencia_porcentaje': diff_percent,
                    'x_diferencia_costo': diff_cost,
                    'x_diferencia_venta': price_sale_diff,

                })
                line.unlink()
        if existings:
            for line_aux in existings:
                line_aux.unlink()

        hijos = self.search([('inventory_parent_id', '=', self.id), ('state', '=', 'confirm')])
        if self.inventory_parent_id and hijos:
            raise UserError('Un inventario padre no puede tener un padre.')
        if not self.inventory_parent_id and hijos:
            # _logger.warning('GRP')
            for hijo in hijos:
                if hijo.location_id.id != self.location_id.id:
                    raise UserError(
                        'El inventario ' + hijo.name + ' hijo debe tener el mismo almacen para inventariar.')
                existings = []
                for line in hijo.line_ids:
                    existings = self.env['stock.inventory.line'].search([
                        ('id', '!=', line.id),
                        ('product_id', '=', line.product_id.id),
                        ('inventory_id.state', '=', 'confirm'),
                        ('location_id', '=', line.location_id.id),
                        ('partner_id', '=', line.partner_id.id),
                        ('package_id', '=', line.package_id.id),
                        ('inventory_id', '=', line.inventory_id.id),
                        ('prod_lot_id', '=', line.prod_lot_id.id)], )
                    for line_aux in existings:
                        '''
                        
                        if line.theoretical_qty > 0:
                    diff_percent = round((((line.product_qty + line_aux.product_qty) - line_aux.theoretical_qty) * 100)
                                         / line.theoretical_qty, 2)
                else:
                    diff_percent = 100
                diff_cost = ((line.product_qty + line_aux.product_qty) - line_aux.theoretical_qty) * self.env[
                    'product.template'].browse(
                    line.product_id.id).standard_price
                price_sale_diff = ((line.product_qty + line_aux.product_qty) - line_aux.theoretical_qty) * self.env[
                    'product.template'].browse(
                    line.product_id.id).list_price
    
                line_aux.write({
                    'product_qty': line.product_qty + line_aux.product_qty,
                    'x_diferencia_cantidad': (line.product_qty + line_aux.product_qty) - line_aux.theoretical_qty,
                    'x_diferencia_porcentaje': diff_percent,
                    'x_diferencia_costo': diff_cost,
                    'x_diferencia_venta': price_sale_diff,
    
                })
                        
                        '''
                        line_aux.write({
                            'product_qty': line.product_qty + line_aux.product_qty
                        })
                        line.unlink()
                if existings:
                    for line_aux in existings:
                        line_aux.unlink()

        if not self.inventory_parent_id and hijos:
            # _logger.warning('GRP')
            for hijo in hijos:
                for son_line in hijo.line_ids:
                    exists_son = False
                    for parent_line in self.line_ids:
                        if son_line.product_id.id == parent_line.product_id.id:
                            exists_son = True
                            son_qty = son_line.product_qty
                            parent_qty = parent_line.product_qty
                            parent_line.write({
                                'product_qty': son_qty + parent_qty
                            })
                    if not exists_son:
                        son_line.write({
                            'inventory_id': parent_line.inventory_id.id
                        })

                hijo.write({
                    'state': 'done'
                })

    '''def update_inventory_quantities(self):
        for line in self.line_ids:
            line.write({'theoretical_qty': self.env['stock.quant'].search(
                [('company_id', '=', self.env.user.company_id.id), ('location_id', '=', self.location_id.id),
                 ('product_id', '=', line.product_id.id)]).quantity})'''

    def _default_location_id(self):
        if self.env.user.has_group('stock.group_stock_manager'):
            company_user = self.env.user.company_id
            warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
            if warehouse:
                return warehouse.lot_stock_id.id
            else:
                raise UserError(_('You must define a warehouse for the company: %s.') % (company_user.name,))
        else:
            return self.env.user.inventory_stock_location_id.id
