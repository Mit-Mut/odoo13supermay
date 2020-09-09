from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError
from datetime import datetime, date, time, timedelta
import pytz
import logging

_logger = logging.getLogger(__name__)


class StockReportWizard(models.TransientModel):
    _name = 'stock.report.wizard.smay'
    _description = 'Saves data for stock report for Super May'

    start_date = fields.Date(string='Fecha de Inventario', )
    agrega_ceros = fields.Boolean(string='Agrega prods. en 0.', default=False)
    costo_promedio = fields.Boolean(string='Costo Promedio', required=True, default=False)
    sucursal_id = fields.Selection(selection=lambda self: self.get_branches(), string='Sucursal', default='0',
                                   required=True, )

    def get_branches(self):
        almacenes = self.env['stock.location'].search([('active', '=', True), ('usage', '=', 'internal')])
        sucursales = []
        for almacen in almacenes:
            sucursal = (almacen.id, almacen.complete_name.replace('Physical Locations/', ''))
            sucursales.append(sucursal)
        sucursal = ('0', 'Todas Las Sucursales')
        sucursales.append(sucursal)
        return sucursales

    def generate_report(self):
        self.env['stock.report.smay']._genera_vista(self.sucursal_id)
        return {
            'name': _("Valoración de Inventario - SMAY"),
            'view_mode': 'pivot',
            'view_id': False,
            'view_type': 'pivot',
            'res_model': 'stock.report.smay',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': '[]',
            'context': None
        }


class StockReportSmay(models.Model):
    _name = 'stock.report.smay'
    _description = 'Vista para guardar la informacion del reporte'
    #_auto = False

    product_id = fields.Many2one('product.product', 'Producto', readonly=True)
    barcode = fields.Char(readonly=True)
    nombre_producto = fields.Char(readonly=True)
    impuestos = fields.Char(readonly=True)
    almacen = fields.Char(readonly=True)
    cantidad = fields.Float(readonly=True)
    qty_reservada = fields.Float(readonly=True)
    qty_total = fields.Float(readonly=True)
    last_price_unit = fields.Float(readonly=True)
    last_price_total = fields.Float(readonly=True)

    def _genera_vista(self, location_id):
        condicional = ''
        if int(location_id) > 0:
            condicional = 'and sl.id = ' + str(location_id)
        tools.drop_view_if_exists(self._cr, self._table)
        '''self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT  1 as "id",
                        pp.barcode as "barcode",
                        pp.id as "product_id",
                        pt.name as "nombre_producto",
                        at.name as "impuestos", 
                        replace(sl.complete_name,'Physical Locations','') as "almacen",                     
                        sq.quantity as "cantidad",
                        sq.reserved_quantity as "qty_reservada",
                        ultimo_costo.ultimo_costo as "last_price_unit",
                        (sq.quantity+sq.reserved_quantity) as "qty_total",                   
                        (sq.quantity+sq.reserved_quantity)*ultimo_costo.ultimo_costo as "last_price_total"
                FROM stock_quant as sq
                RIGHT JOIN product_product as pp
                    ON sq.product_id = pp.id
                JOIN  product_template pt
                    ON pp.product_tmpl_id = pt.id
                JOIN product_taxes_rel ptr
                    ON ptr.prod_id = pt.id
                JOIN account_tax at
                    ON at.id = ptr.tax_id
                    
                JOIN stock_location sl
                    ON sq.location_id = sl.id
                    AND sl.active = true
                JOIN (
                    SELECT product_id as product_id,
                            avg(cost) as costo
                    FROM product_price_history
                    GROUP BY product_id
                ) avg_cost
                    ON avg_cost.product_id = pp.id
                JOIN (
                    SELECT pph2.product_id as product_id, 
                            pph2.cost as "ultimo_costo" 
                    FROM    (			
                            SELECT product_id as product_id,
                                    max(datetime) as fecha
                            FROM product_price_history
                            GROUP BY product_id
                            )  fecha_ult_precio
                    JOIN product_price_history pph2
                        ON fecha_ult_precio.product_id = pph2.product_id
                        AND fecha_ult_precio.fecha = pph2.datetime
                    ) ultimo_costo
                    ON ultimo_costo.product_id = sq.product_id
                WHERE sl.usage='internal' 
                %s
                ORDER BY pt.name,sq.quantity,sl.complete_name
            )
        """ % (self._table, condicional))'''
