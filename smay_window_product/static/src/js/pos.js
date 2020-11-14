odoo.define('smay_window_product.smay_window_product', function(require){
    "use strict";

    var gui = require('point_of_sale.gui');
    var popups = require('point_of_sale.popups');
    var screens = require('point_of_sale.screens');
    var models = require('point_of_sale.models');

    var _super_orderline = models.Orderline;

	models.Orderline = models.Orderline.extend({
		set_quantity: function(quantity, keep_price){
			var self = this;			
			_super_orderline.prototype.set_quantity.apply(this,arguments);
			this.price = this.pos.get_order().redondea_qty(this.price,2)
			if(this.pos.get_order()){
				if(this.price<= this.product.standard_price){
					this.pos.get_order().remove_orderline(this);
					self.pos.gui.show_popup('error',{
						'title': 'Precio de venta Incorrecto',
						'body': 'Solicita al encargado que revise la lista de precios para el producto: '+ this.product.display_name,
					});
				}
				
				if(this.get_quantity()==0)
				    this.pos.get_order().remove_orderline(this);
			}
		},
	});

	var _super_order = models.Order;

	models.Order =models.Order.extend({

	    redondea_qty: function(cantidad,decimales){
	        var power = Math.pow(10, decimales);
	        return Math.round(cantidad*power)/power;
	    },

		add_product: function(product, options){
			var self = this;
			if(product.list_price == 0){
				self.pos.gui.show_popup('error',{
					'title': 'Precio de Venta incorrecto',
					'body': 'Precio de venta mal configurado, solicita la revisión al encargado.',
				});
				return ;
			}


			if(product.list_price <= product.standard_price){
				self.pos.gui.show_popup('error',{
					'title': 'Precio de Venta incorrecto',
					'body': 'Precio de venta es menor al costo, solicita la revisión al encargado.',
				});
				return ;
			}

			_super_order.prototype.add_product.apply(this,arguments);
			var order = self.pos.get_order();
			var orderlines = order.get_orderlines();	
			for(var i=0; i< orderlines.length; i++){
				if(product == orderlines[i].product){
					if(orderlines[i].price<= orderlines[i].product.standard_price){
						order.remove_orderline(orderlines[i]);
						i--;
						self.pos.gui.show_popup('error',{
							'title': 'Precio de venta Incorrecto',
							'body': 'Solicita al encargado que revise la lista de precios para el producto: '+ product.display_name,
						});
					}
				}	
			}
		}
	});

	var InformationProductPopUp = popups.extend({
		template:'InformationProductPopUp',

    	show: function(options){
        	var self = this;
	        self._super(options);
	        var product_id = 0;
        	var qty = 0;

			self.$('.priceProductUnit').on('click',function(){
	            		self.gui.close_popup();
        				product_id = self.$('.priceProductUnit').attr('product_id');
		        		qty = $(this).attr('qty');
				        if(product_id > 0){
	    	               	var product = self.pos.db.get_product_by_id(product_id);
                    		for(var i = 0; i < qty; i++){
			                    if(product.to_weight && self.pos.config.iface_electronic_scale){
                        			self.gui.show_screen('scale',{product: product});
                        		}else{
					                self.pos.get_order().add_product(product);
                        		}
                    		}
	            		}
	        	});



            self.$('#cancel').on('click',function(){
               	self.gui.close_popup();
          	});
	    },
	});

	gui.define_popup({name:'InformationProductPopUp',widget: InformationProductPopUp});

	screens.ProductScreenWidget.include({

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

        click_product: function(product) {
            var self = this;
            var aux_promo = false;
            var promotion = {};
            var stock_qty = self.pos.db.product_by_id[product.id]? self.pos.db.product_by_id[product.id].qty_available : 0

            self.gui.show_popup('InformationProductPopUp',{
                'title': product.display_name,
                'id': product.id,
                'url_image': self.pos.attributes.origin+"/web/image?model=product.product&field=image_1024&id="+product.id,
                'stock_qty': stock_qty,
                'prices':self.get_prices_by_list(product),
                'cost': self.pos.db.product_by_id[product.id]? self.pos.db.product_by_id[product.id].standard_price : 0,
            });
       	},
	});
 });
