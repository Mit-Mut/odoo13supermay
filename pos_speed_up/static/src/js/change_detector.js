/*
* @Author: D.Jane
* @Email: jane.odoo.sp@gmail.com
*/
odoo.define('pos_speed_up.change_detector', function (require) {
    "use strict";
    var chrome = require('point_of_sale.chrome');
    var rpc = require('web.rpc');
    var indexedDB = require('pos_speed_up.indexedDB');
    var models = require('point_of_sale.models');
    var ProductListWidget = require('point_of_sale.screens').ProductListWidget;
    var Bus = require('bus.Longpolling');
    var gui = require('point_of_sale.gui');

    if (!indexedDB) {
        return;
    }

    var _super_pos = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            this.count_sync = 0;
	self= this;
//:wq
		//self.synch_without_reload();
            _super_pos.initialize.call(this, session, attributes);
		
        },
        synch_without_reload: function (change_detector) {
            change_detector.set_status('connecting');

            var self = this;
	    
/*	   products.forEach(function(product){
		product.qty_available = 14;
		   product.virtual_available = 14;
	   });*/

            $.when(indexedDB.get('products'), indexedDB.get('customers')).then(function (products, customers) {

		//code added by GRP
		/*var i=0;
		products.forEach(function(product){
			product.qty_available =i;
			product.virtual_available=i;
			//i++;
		});
*/
		rpc.query({
			model: 'product.index',
			method: 'get_real_qty',
			args:[
				self.config.company_id[0],
				self.config.stock_location_id[0],
				//Object.keys(self.get('wk_product_qtys')).map(function(item){ return parseInt(item,10)}),
			],
			timeout:2000,
		}).then(function(stocks){
			if(self.gui.get_current_screen() == 'products' && 
				self.gui.current_popup==null && 
				$('.searchbox input')[0].value!=''){ 
				 return;
		  	}
			//console.log('productssss')
			//console.log(products)
			products.forEach(function(product){
				product.qty_available = stocks[product.id] ? stocks[product.id] : 0
				product.virtual_available = stocks[product.id] ? stocks[product.id] : 0
			});
			//console.log(products)

			self.set({'wk_product_qtys':stocks});

                	indexedDB.order_by_in_place(products, ['sequence', 'default_code', 'name'], 'esc');


		if(self.gui.get_current_screen() =='products' && self.gui.current_popup == null){
                self.db.product_by_category_id = {};
                self.db.category_search_string = {};}

		self.p_super_loaded(self,products);


                // add customer
                self.c_super_loaded(self, customers);

                // re-render products
                var products_screen = self.gui.screen_instances['products'];
                products_screen.product_list_widget = new ProductListWidget(products_screen, {
                    click_product_action: function (product) {
                        products_screen.click_product(product);
                    },
                    product_list: self.db.get_product_by_category(products_screen.product_categories_widget.category.id)
                });
                products_screen.product_list_widget.replace($('.product-list-container'));
                products_screen.product_categories_widget.product_list_widget = products_screen.product_list_widget;
                // -end-

                setTimeout(function () {
                    change_detector.set_status('connected');
                }, 500);

                // reset count
                self.count_sync = 0;
					
		if(self.gui.get_current_screen() == 'products' && self.gui.current_popup == null)
	        self.gui.show_screen('products', null, true);
//			self.set({'wk_product_qtys': stocks});
                
		}).fail(function(error){
			console.log(error)
		});
		   

		/*if(self.gui.get_current_screen() == 'products' && 
			self.gui.current_popup==null && 
			$('.searchbox input')[0].value!=''){ 
			 return;
		  }
		    console.log(products)*/
                // order_by product
//                indexedDB.order_by_in_place(products, ['sequence', 'default_code', 'name'], 'esc');

                // add product
//		if(self.gui.get_current_screen() =='products' && self.gui.current_popup == null){
//                self.db.product_by_category_id = {};
//                self.db.category_search_string = {};}

                //self.p_super_loaded(self, products);
	/*	rpc.query({
			model: 'product.index',
			method: 'get_real_qty',
			////
//			product_ids:Object.keys(self.get('wk_product_qtys')).map(function(item){return parseInt(item,10)}),
			//
			args: [
				self.config.company_id[0],
				self.config.stock_location_id[0],
				Object.keys(self.get('wk_product_qtys')).map(function(item){ return parseInt(item,10)}),
			],
			timeout: 2000,
		}).then(function(stocks){
			console.log('stockssssss');
			console.log(stocks);
			console.log(self.get('wk_product_qtys'))

			console.log(JSON.stringify(stocks)== JSON.stringify(self.get('wk_product_qtys')))
			self.set({'wk_product_qtys': stocks});
			//products.forEach(function(product){
				//console.log('product');
				//console.log(product);
			//});
			//self.p_super_loaded(self, products);

		}).fail(function(error){
			console.log('error');
		});*/
/*
                // add customer
                self.c_super_loaded(self, customers);

                // re-render products
                var products_screen = self.gui.screen_instances['products'];
                products_screen.product_list_widget = new ProductListWidget(products_screen, {
                    click_product_action: function (product) {
                        products_screen.click_product(product);
                    },
                    product_list: self.db.get_product_by_category(products_screen.product_categories_widget.category.id)
                });
                products_screen.product_list_widget.replace($('.product-list-container'));
                products_screen.product_categories_widget.product_list_widget = products_screen.product_list_widget;
                // -end-

                setTimeout(function () {
                    change_detector.set_status('connected');
                }, 500);

                // reset count
                self.count_sync = 0;*/

		//update stock
		//console.log('thisssss');
		//console.log(this)
		//console.log(self);
		/*rpc.query({
			model: 'product.index',
			method: 'get_real_qty',
			args: [
				self.config.company_id[0],
				self.config.stock_location_id[0],
			      ],
			timeout: 2000,
		}).then(function(stocks){
		//	console.log('stocks');
		//	console.log(stocks);
			console.log('fecha1')
			console.log(new Date())
			setTimeout(function(){
				self.set({'wk_product_qtys': stocks});
		//		console.log(self.get('wk_product_qtys'));
				//self.chrome.wk_change_qty_css();
				//self.gui.show_screen('products', null, true);
				//self.p_super_loaded(self, products)
				if(self.gui.get_current_screen() == 'products' && self.gui.current_popup == null){
					console.log('ENTRO AQIOQIAOIAOIS');
				self.gui.show_screen('payment');
				self.gui.show_screen('products');
			        //self.p_super_loaded(self,products);
				//self.gui.show_screen('products',null,true);

				}
				console.log('fecha 2');
				console.log(new Date());
				
			},100);
		}).fail(function(error){
		 console.log('pos_speed no actualizó el stock del almacen asignado el en punto de venta');
		});*/
		/*if(self.gui.get_current_screen() == 'products' && self.gui.current_popup == null){
			console.log('actualiza');
		self.p_super_loaded(self,products);
	        self.gui.show_screen('products', null, true);
	}*/

            }).fail(function () {
                change_detector.set_status('disconnected', self.count_sync);
            });
        }
    });

    var ChangeDetectorWidget = chrome.StatusWidget.extend({
        template: 'ChangeDetectorWidget',

        set_status: function (status, msg) {
            for (var i = 0; i < this.status.length; i++) {
                this.$('.jane_' + this.status[i]).addClass('oe_hidden');
            }
            this.$('.jane_' + status).removeClass('oe_hidden');

            if (msg) {
                this.$('.jane_msg').removeClass('oe_hidden').text(msg);
            } else {
                this.$('.jane_msg').addClass('oe_hidden').html('');
            }
        },
        start: function () {
            var self = this;

            var bus  = new Bus(this.chrome);
            bus.on('notification', this, this._onNotification);
            bus.startPolling();

            this.$el.click(function () {
                self.pos.synch_without_reload(self);
            });
	
		setTimeout(function(){
			$('.js_synch').click();
			$('.jane_msg').hide();
			$('.jane_connected').hide();
			$('.jane_connecting').hide();
			$('.jane_disconnecting').hide();
			$('.jane_error').hide();
		//	self.pos.gui.show_screen('products', null, true);
			
		},500);
        },
        _onNotification: function (notifications) {
            //console.log('vao day', notifications);
            var data = notifications.filter(function (item) {
                return item[0][1] === 'change_detector';
            }).map(function (item) {
                return item[1];
            });

            var p = data.filter(function (item) {
                return item.p;
            });
            var c = data.filter(function (item) {
                return item.c;
            });
            this.on_change(p, c);
        },
        on_change: function (p, c) {
            if (p.length > 0) {
                this.p_sync_not_reload(p.p);
            }

            if (c.length > 0) {
                this.c_sync_not_reload(c.c);
            }

		setTimeout(function(){
			$('.js_synch').click();
	//		$('.jane_msg').click();
			$('.jane_connected').hide();
			$('.jane_connecting').hide();
			$('.jane_disconnecting').hide();
			$('.jane_error').hide();
		},500);


        },
        p_sync_not_reload: function (server_version) {
            var self = this;

            var model = self.pos.get_model('product.product');

            var client_version = localStorage.getItem('product_index_version');
            if (!/^\d+$/.test(client_version)) {
                client_version = 0;
            }

            if (client_version === server_version) {
                return;
            }

            rpc.query({
                model: 'product.index',
                method: 'sync_not_reload',
                args: [client_version, model.fields]
            }).then(function (res) {
                localStorage.setItem('product_index_version', res['latest_version']);

                // increase count
                self.pos.count_sync += res['create'].length + res['delete'].length;

                if (self.pos.count_sync > 0) {
                    self.set_status('disconnected', self.pos.count_sync);
                }

                indexedDB.get_object_store('products').then(function (store) {
                    _.each(res['create'], function (record) {
                        store.put(record).onerror = function (e) {
                            console.log(e);
                            localStorage.setItem('product_index_version', client_version);
                        }
                    });
                    _.each(res['delete'], function (id) {
                        store.delete(id).onerror = function (e) {
                            console.log(e);
                            localStorage.setItem('product_index_version', client_version);
                        };
                    });
                }).fail(function (error) {
                    console.log(error);
                    localStorage.setItem('product_index_version', client_version);
                });
            });
        },
        c_sync_not_reload: function (server_version) {
            var self = this;

            var model = self.pos.get_model('res.partner');

            var client_version = localStorage.getItem('customer_index_version');
            if (!/^\d+$/.test(client_version)) {
                client_version = 0;
            }

            if (client_version === server_version) {
                return;
            }

            rpc.query({
                model: 'customer.index',
                method: 'sync_not_reload',
                args: [client_version, model.fields]
            }).then(function (res) {
                localStorage.setItem('customer_index_version', res['latest_version']);

                self.pos.count_sync += res['create'].length + res['delete'].length;

                if (self.pos.count_sync > 0) {
                    self.set_status('disconnected', self.pos.count_sync);
                }

                indexedDB.get_object_store('customers').then(function (store) {
                    _.each(res['create'], function (record) {
                        store.put(record).onerror = function (e) {
                            console.log(e);
                            localStorage.setItem('customer_index_version', client_version);
                        }
                    });
                    _.each(res['delete'], function (id) {
                        store.delete(id).onerror = function (e) {
                            console.log(e);
                            localStorage.setItem('customer_index_version', client_version);
                        };
                    });
                }).fail(function (error) {
                    console.log(error);
                    localStorage.setItem('customer_index_version', client_version);
                });

                // clear dom cache for re-render customers
                var partner_screen = self.gui.screen_instances['clientlist'];
                var partner_cache = partner_screen.partner_cache;
                res['create'].map(function (partner) {
                    return partner.id;
                }).concat(res['delete']).forEach(function (partner_id) {
                    partner_cache.clear_node(partner_id);
                });

/*		    console.log('FFFFFFF');
		    console.log(self.pos.config.company_id[0])
		    console.log(self.pos.config.stock_location_id[0])
		    rpc.query({
			    model:'product.index',
			    method: 'get_real_qty',
			    args: [self.pos.config.company_id[0],
			    	self.pos.config.stock_location_id[0]],
			    timeout: 2000,
		    
		    }).then(function(stocks){
			    console.log('stoks')
			    console.log(stocks)
			    setTimeout(function(){
			    self.pos.set({'wk_product_qtys':stocks})
			    console.log(self.pos.get('wk_product_qtys'))
		            self.chrome.wk_change_qty_css();
		            //self.ProductListWidget.renderElement();
		            self.gui.show_screen('products', null, true);
		            self.gui.show_screen('payment')
		            self.gui.show_screen('products')
			    },3000);
			    
		    }).fail(function(error){
			    console.log('error pos_speed')

		    });*/
            });
        }
    });


    chrome.SynchNotificationWidget.include({
        renderElement: function () {
            new ChangeDetectorWidget(this, {}).appendTo('.pos-rightheader');
            this._super();
        }
    });

});
