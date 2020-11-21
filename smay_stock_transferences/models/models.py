# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

'''
FECHA:		20201120 
VERSIÓN:	v13.0.0.1:
DESCRIPCIÓN:
		En la configuración del punto de venta añade los siguientes campos para poner restriccciones de venta y visualización
		
MODELO: res.users
CAMPOS:
    
    stock_location_id = fields.Many2one('stock.location', string='Almacen origen para transferencias',
                                        domain="[('name','=','Stock')]")

    transfers_validator = fields.Boolean(string='Puede validar transferencias', default=False)

    picking_type_id = fields.Many2one('stock.picking.type', string='Tipo de movimiento por default',
                                      domain="[('name','=','Transferencias internas')]")    
'''


class smayTransferencesResUser(models.Model):
    _inherit = 'res.users'

    stock_location_id = fields.Many2one('stock.location', string='Almacen origen para transferencias',
                                        domain="[('name','=','Stock')]")

    transfers_validator = fields.Boolean(string='Puede validar transferencias', default=False)

    picking_type_id = fields.Many2one('stock.picking.type', string='Tipo de movimiento por default',
                                      domain="[('name','=','Transferencias internas')]")

    sucursal_transferencias_id = fields.Many2one('res.partner', 'Sucursal Transferencias')


class smayTransferencesStockPicking(models.Model):
    _inherit = 'stock.picking'

    partner_id = fields.Many2one(
        'res.partner', 'Partner',
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        default=lambda self: self.env.user.sucursal_transferencias_id.id)

    location_id = fields.Many2one(
        'stock.location', "Source Location",
        default=lambda self: self._default_location(),
        readonly=True, required=True,
        states={'draft': [('readonly', False)]})

    @api.onchange('move_ids_without_package.product_id')
    def _change_productttt(self):
        _logger.warning('WWWWWWWWWWWWWWWWWWW'+str(self.move_ids_without_package))
        for move in self.move_ids_without_package:
            if move.product_uom_qty==0:
                _logger.warning(str(move.product_id))
                move.product_uom_qty =100

    @api.model
    def _default_location(self):
        if self.env.user.has_group('stock.group_stock_manager'):
            return
        else:
            return self.env.user.stock_location_id.id

    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type',
        required=True,
        readonly=True,
        domain="[('name','=','Transferencias internas')]",
        states={'draft': [('readonly', False)]}, default=lambda self: self._default_picking_type())

    @api.model
    def _default_picking_type(self):
        if self.env.user.has_group('stock.group_stock_manager'):
            return
        else:
            return self.env.user.picking_type_id.id

    def write2(self, vals):
        self.validate_picking(vals)
        record = super(smayTransferencesStockPicking, self).write(vals)
        self.validate_picking_records()

        return record

    @api.model
    def create2(self, vals):
        self.validate_picking(vals)
        record = super(smayTransferencesStockPicking, self).create(vals)
        self.validate_picking_records()
        return record

    def validate_picking_records(self):

        i = 0
        '''if not self.id:
            if len(self.browse(self.id).move_ids_without_package) == 0:
                raise UserError('La transferencia debe tener productos agregados.')'''
        for picking in self.move_ids_without_package:
            j = 0
            for picking_aux in self.move_ids_without_package:
                if i != j and picking.product_id.id == picking_aux.product_id.id:
                    raise UserError('El product ' + str(picking_aux.product_id.name) + ' esta repetido')
                j = j + 1
            i = i + 1

        for picking in self.move_ids_without_package:

            stocks = self.env['stock.quant'].search([('company_id', '=', self.env.user.company_id.id),
                                                     ('location_id', '=', self.location_id.id),
                                                     ('product_id', '=', picking.product_id.id)]).quantity
            if stocks <= 0:
                raise UserError('No tienes stock para transferir del producto ' + str(picking.product_id.name))
            if stocks < picking.product_uom_qty:
                raise UserError('No puedes transferir ' + str(picking.product_uom_qty) + ' piezas del producto ' + str(
                    picking.product_id.name) + ', solo cuentas con ' + str(stocks) + ' piezas en tu almacen.')

    def validate_picking(self, vals):
        i = 0
        if vals.get('move_ids_without_package'):
            for picking in vals.get('move_ids_without_package'):
                if picking[0] == 0:
                    if picking[2].get('product_uom_qty') <= 0:
                        raise UserError(
                            'El producto ' + str(picking[2].get('name')) + ' debe tener una cantidad mayor a 0')
                    j = 0
                    for picking_aux in vals.get('move_ids_without_package'):
                        if picking_aux[0] == 0:
                            if j != i and picking[2].get('product_id') == picking_aux[2].get('product_id'):
                                raise UserError('El producto ' + str(self.env['product.product'].browse(
                                    picking[2].get('product_id')).name) + ' esta repetido.')
                            j = j + 1
                    i = i + 1

    def validation_lines(self):
        for picking in self.move_ids_without_package:

            stocks = self.env['stock.quant'].search([('company_id', '=', self.env.user.company_id.id),
                                                     ('location_id', '=', self.location_id.id),
                                                     ('product_id', '=', picking.product_id.id)]).quantity
            if picking.product_uom_qty <= 0:
                raise UserError('La cantidad del producto ' + str(picking.product_id.name) + ' debe ser mayor a 0')
            if stocks <= 0:
                raise UserError(
                    str(stocks) + 'No tienes stock para transferir del producto ' + str(picking.product_id.name))
            if stocks < picking.product_uom_qty:
                raise UserError('No puedes transferir ' + str(picking.product_uom_qty) + ' piezas del producto ' + str(
                    picking.product_id.name) + ', solo cuentas con ' + str(stocks) + ' piezas en tu almacen.')

            for picking_aux in self.move_ids_without_package:
                if picking_aux.id != picking.id and picking.product_id.id == picking_aux.product_id.id:
                    raise UserError('El producto ' + str(picking.product_id.name) + ' esta repetido.')

        if self.id:
            '''raise UserError(str(self.location_id.id) + '   ' + str(self.location_id.name) + '   dest:' + str(
                self.location_dest_id.id) + '   ' + str(self.location_dest_id.name) + 'self' + str(self))'''
            if self.location_id.id == self.location_dest_id.id:
                raise UserError('La ubicación origen y destino no pueden ser la misma.')

    # @api.multi
    def action_confirm(self):
        if '/INT/' in str(self.name):
            if self.id:
                self.validation_lines()
                '''raise UserError(str(self.location_id.id) + '   ' + str(self.location_id.name) + '   dest:' + str(
                    self.location_dest_id.id) + '   ' + str(self.location_dest_id.name) + 'self' + str(self))'''
                if self.location_id.id == self.location_dest_id.id:
                    raise UserError('La ubicación origen y destino no pueden ser la misma.')

                if self.env.user.has_group('stock.group_stock_manager'):
                    return super(smayTransferencesStockPicking, self).action_confirm()
                else:
                    if self.location_dest_id.name in ('Mermas', 'Insumos'):
                        raise UserError('Solo los administradores pueden validar envios a Merma o Insumos')

                    if self.location_id.id == self.location_dest_id.id:
                        raise UserError('La ubicación origen y destino no pueden ser la misma.')

                    if self.location_id.id != self.env.user.stock_location_id.id:
                        raise UserError(
                            'Solo un usuario de la sucursal que envia puede marcar por realizar la transferencia.')
                    else:
                        return super(smayTransferencesStockPicking, self).action_confirm()
            else:
                return super(smayTransferencesStockPicking, self).action_confirm()
        else:
            return super(smayTransferencesStockPicking, self).action_confirm()

    # @api.multi
    def button_validate(self):
        if '/INT/' in str(self.name):
            self.validation_lines()
            if self.env.user.has_group('stock.group_stock_manager'):
                return super(smayTransferencesStockPicking, self).button_validate()
            else:
                if not self.env.user.transfers_validator:
                    raise UserError('No tienes lo privilegios para validar transferencias de inventario')
                else:
                    if self.location_dest_id.id != self.env.user.stock_location_id.id:
                        raise UserError('No puedes validar transferencias para el almacen de otra sucursal')
                return super(smayTransferencesStockPicking, self).button_validate()

        else:
            return super(smayTransferencesStockPicking, self).button_validate()

    '''@api.multi
    def button_validate(self):
        if self.env.user.has_group('stock.group_stock_manager'):
            return super(smayTransferencesStockPicking, self).button_validate()
        else:
            if not self.env.user.transfers_validator or not self.env.user.purchase_validator:
                raise UserError('No tienes lo privilegios para validar transferencias de inventario')
            if self.location_dest_id.id != self.env.user.stock_location_id.id:
                raise UserError('No puedes validar transferencias para el almacen de otra sucursal')
            return super(smayTransferencesStockPicking, self).button_validate()'''

    # @api.multi
    def action_assign(self):
        if '/INT/' in str(self.name):
            self.validation_lines()
            if self.env.user.has_group('stock.group_stock_manager'):
                super(smayTransferencesStockPicking, self).action_assign()
            else:
                if self.location_id.id != self.env.user.stock_location_id.id:
                    raise UserError('Solo puedes comprobrar disponibilidad de la sucursal asignada.')
                super(smayTransferencesStockPicking, self).action_assign()
        else:
            return super(smayTransferencesStockPicking, self).action_assign()

    # @api.multi
    def do_unreserve(self):
        if '/INT/' in str(self.name):
            if self.env.user.has_group('stock.group_stock_manager'):
                super(smayTransferencesStockPicking, self).do_unreserve()
            else:
                if self.location_dest_id.id != self.env.user.stock_location_id.id:
                    raise UserError(
                        'Solo puedes cancelar la disponibilidad del las transferencias de la sucursal que tienes asignada.')
                else:
                    super(smayTransferencesStockPicking, self).do_unreserve()
        else:
            super(smayTransferencesStockPicking, self).do_unreserve()

    def action_toggle_is_locked(self):
        if '/INT/' in str(self.name):
            raise UserError('Funcionalidad deshabilidata.')
        return super(smayTransferencesStockPicking, self).action_toggle_is_locked()

    def button_scrap(self):
        if '/INT/' in str(self.name):
            raise UserError('Funcionalidad deshabilitada.')
        return super(smayTransferencesStockPicking, self).button_scrap()


class smayTransferencesReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'


class smayTransferencesReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def create_returns(self):
        if self.env.user.has_group('stock.group_stock_manager'):
            super(smayTransferencesReturnPicking, self).create_returns()
        else:
            raise UserError('No tienes los permisos para realizar la devolución de la transferencia.')
