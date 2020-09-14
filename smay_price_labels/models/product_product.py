# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SmayPriceProduct(models.Model):
    _inherit = 'product.product'

    def get_prices_smay(self, product_id):
        prices = {}
        aux_price = self.env['product.pricelist'].browse(
            self.env.user.partner_id.property_product_pricelist.id).get_product_price(self.browse(product_id), 1,
                                                                                      self.env.user.partner_id)
        prices[1] = aux_price
        for i in range(120):
            if i > 1:
                aux_price2 = self.env['product.pricelist'].browse(
                    self.env.user.partner_id.property_product_pricelist.id).get_product_price(self.browse(product_id),
                                                                                              i,
                                                                                              self.env.user.partner_id)
                if aux_price != aux_price2:
                    prices[i] = self.env['product.pricelist'].browse(
                        self.env.user.partner_id.property_product_pricelist.id).get_product_price(
                        self.browse(product_id), i, self.env.user.partner_id)
                    aux_price = aux_price2
        return prices


class SamyProductPricelist(models.Model):
    _inherit = "product_pricelist"

    def get_product_price(self, product, quantity, partner, date=False, uom_id=False):
        price = super(SamyProductPricelist, self).get_product_price(self, product, quantity, partner, date=False,
                                                                    uom_id=False)
        return round(price, 1)
