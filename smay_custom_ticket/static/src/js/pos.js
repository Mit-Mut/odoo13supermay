odoo.define('smay_custom_ticket.smay_custom_ticket', function(require){
    "use strict";

    var models = require('point_of_sale.models');
	var screens = require('point_of_sale.screens');

	//models.load_fields('res.company', ['vat', 'street','street2','city','state_id','zip','country_id','phone',])//'street_number','l10n_mx_edi_colony','l10n_mx_edi_locality'])
	models.load_fields('res.company', ['vat', 'street','street2','city','state_id','zip','country_id','phone','street_number','l10n_mx_edi_colony','l10n_mx_edi_locality'])
	models.load_fields('res.users', ['is_manager'])
	models.load_fields('res.partner',['l10n_mx_edi_colony','street_name','street_number'])

	var _super_orderline = models.Orderline;
    models.Orderline = models.Orderline.extend({

        export_for_printing: function(){
            var data = _super_orderline.prototype.export_for_printing.call(this,arguments);
            var price = self.pos.db.get_product_by_id(data.product_id)
            data['price_without_discount'] = this.get_product().lst_price;
            return data
        },
    });

    screens.OrderWidget.include({
        update_summary: function(){
            var self = this;
            self._super();
            var order = this.pos.get_order();
            var orderlines = order.get_orderlines();
            var total     = order ? order.get_total_with_tax() : 0;
            var taxes     = order ? total - order.get_total_without_tax() : 0;
            var total_descuento =0;
            for(var i=0; i< order.get_orderlines().length; i++){
                if(orderlines[i].price< orderlines[i].product.lst_price )
                    total_descuento += (orderlines[i].product.lst_price - orderlines[i].price)*orderlines[i].quantity;
                }

                setTimeout(function(){
                    $('.subtotalSmay').children('span').text(self.format_currency(order.get_total_with_tax()+total_descuento));
                    $('.descuentoSmay').children('span').text(self.format_currency(total_descuento));
                    //$('.taxesSmay').children('span').text(self.format_currency(taxes));
                },100);
            },
        });


	var _super_order = models.Order;
	models.Order = models.Order.extend({
        get_qty_products(){
            var qty = 0;
            for(var i in this.get_orderlines() ){
                qty=qty+this.get_orderlines()[i].quantity
            }
            return qty
        },
    });
});
