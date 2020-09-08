odoo.define('smay_check_prices.smay_check_prices', function(require){
    "use strict";

    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');

    var _super_OrderWidget = screens.OrderWidget;
    _super_OrderWidget  = screens.OrderWidget.include({
        init: function(parent, options){
            this._super(parent, options);

            setTimeout(function(){
                if(self.pos.config.es_checador_precios){
                    $('.username').hide();
                    $('.control-buttons').hide();
                    $('.neworder-button').hide();
                    $('.deleteorder-button').hide();
                    $('.smay_menu').hide();
                    $('.header-button').hide();
                    $('.js_synch').hide();
                    $('.set-customer').toggleClass('disabled-mode',false).prop('disabled', true);
                    $('.button.pay').toggleClass('disabled-mode',true).prop('disabled', true);
                    $('.mode-button[data-mode="price"]').toggleClass('disabled-mode', true).prop('disabled', true);
                    $('.mode-button[data-mode="discount"]').toggleClass('disabled-mode', true).prop('disabled', true);
                }
            },500)
        }
    });
	
	var _super_ProductScreenWidget = screens.ProductScreenWidget
    _super_ProductScreenWidget = screens.ProductScreenWidget.include({

    click_product: function(product) {
			this._super(product);
			if(self.pos.config.es_checador_precios){
			//setTimeout(function(){
			    if(!self.pos.config.mostrar_existencias)
			        $('.priceProduct').hide()//, 500})

			    setTimeout(function(){
				self.gui.close_popup();
				},5000)
			}
       	},
    });


    var _super_order = models.Order;
    models.Order = models.Order.extend({
        export_as_JSON: function (){
            var data = _super_order.prototype.export_as_JSON.apply(this, arguments);
            if(self.pos.gui.get_current_screen()){
                if(self.pos.gui.get_current_screen()!='products' && self.pos.config.es_checador_precios)
                    self.pos.gui.show_screen('products')
            }
            return data;
        },

        add_product: function(product, options){


            if(self.pos.config.es_checador_precios){

                for(var i= this.get_orderlines().length ; i>=0; i--){
                    this.remove_orderline(this.get_orderlines()[i])
                }
                var stock_qty = self.pos.db.product_by_id[product.id]? self.pos.db.product_by_id[product.id].qty_available : 0
       			self.gui.show_popup('InformationProductPopUp',{
                    'title': product.display_name,
           			'id': product.id,
	    			'url_image': self.pos.attributes.origin+"/web/image?model=product.product&field=image_512&id="+product.id,
	           		'stock_qty': stock_qty,
		    		'prices':this.get_prices_by_list(product),
			    	'cost': self.pos.db.product_by_id[product.id]? self.pos.db.product_by_id[product.id].standard_price : 0,
			    });
				
				setTimeout(function(){
				self.gui.close_popup();
				},5000)
				if(!self.pos.config.mostrar_existencias)
			        $('.priceProduct').hide()
			    $('.priceProductUnit').off('click')
            }

            if(self.pos.config.es_checador_precios && this.get_orderlines().length==0){
                _super_order.prototype.add_product.apply(this, arguments);
            }else{
                _super_order.prototype.add_product.apply(this, arguments);
            }
        },


        get_prices_by_list: function(product){
			var price = {};
			var prices =[];
			var temp_price = 0;
			var pricelist = self.pos.get_order().pricelist;

			for(var i=1; i<=100; i++){
				if(temp_price != product.get_price(pricelist,i).toFixed(2)){
					temp_price = product.get_price(pricelist,i).toFixed(2);
					price[i.toString()] = (product.get_price(pricelist,i).toFixed(2)<=0)? "Configurar": product.get_price(pricelist,i).toFixed(2);
					prices.push(price)
					price = {};
				}
				price={};
			}
			return prices;
		},
    });
});
