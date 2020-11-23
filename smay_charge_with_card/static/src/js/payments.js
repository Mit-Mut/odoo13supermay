odoo.define('smay_charge_with_card.smay_charge_with_card', function(require){
    "use strict";

    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var popups = require('point_of_sale.popups');
    var gui = require('point_of_sale.gui');
    var field_utils = require('web.field_utils');

    models.load_fields('pos.payment.method', ['uso_terminal_smay'])


    var _super_OrderWidget = screens.OrderWidget;
    _super_OrderWidget  = screens.OrderWidget.include({
        init: function(parent, options){
            this._super(parent, options)

            //limpio la orden al recargar el punto de venta
            setTimeout(function(){
                if(self.pos.get_order())
                self.pos.get_order().remove_all_paymentlines()
                    /*for(var i= 0; i<self.pos.get_order().get_orderlines().length; i++){
                        self.pos.get_order().remove_orderline(self.pos.get_order().get_orderlines()[i])
                         i--
                    }*/
            },300)
        }
    });


    var BankReferencePopUp = popups.extend({
		template:'BankReferencePopUp',

    	show: function(options){
        	var self = this;
	        self._super(options);
			
			
			
			
			self.pos.gui.screen_instances.payment.renderElement()
	        $('#confirm').hide()

	        self.$('#confirm').on('click',function(){
                if($('#bank_reference').val()=='' || $('#bank_reference').val().length!=6 ){
                    self.pos.gui.show_popup('error',{
                        'title': 'Error de valor ingresado',
                        'body': 'El valor ingresado es incorrecto, no debe ser vacio o diferente de 6 digitos',
                    })
                    self.pos.get_order().remove_all_paymentlines();
                    self.pos.get_order().x_bank_reference = $('#bank_reference').val()
                    self.pos.gui.screen_instances.payment.renderElement()
                    return
                }
                self.gui.close_popup();
               	self.pos.get_order().x_bank_reference = $('#bank_reference').val()
               	$('.button.next.highlight').click()
          	});

            self.$('#cancel').on('click',function(){
                self.pos.get_order().x_bank_reference =''
                self.pos.get_order().remove_all_paymentlines();
                self.gui.close_popup();
                self.pos.gui.screen_instances.payment.renderElement()
          	});
	    },
	});

	gui.define_popup({name:'BankReferencePopUp',widget: BankReferencePopUp});



    var _super_ActionpadWidget = screens.ActionpadWidget;

    _super_ActionpadWidget = screens.ActionpadWidget.include({

        ///Inherited Functions
        renderElement: function() {
            var self = this;
            this._super();
            this.$('.pay').click(function(){
                var order = self.pos.get_order();
                var has_valid_product_lot = _.every(order.orderlines.models, function(line){
                    return line.has_valid_product_lot();
                });
                if(!has_valid_product_lot){
                    self.gui.show_popup('confirm',{
                        'title': _t('Empty Serial/Lot Number'),
                        'body':  _t('One or more product(s) required serial/lot number.'),
                        confirm: function(){
                            self.gui.show_screen('payment');
                        },
                    });
                }else{
                    if(order.get_total_with_tax()!= 0 && order.get_orderlines().length > 0){
                        self.gui.show_screen('payment');
                        }else{
                        self.gui.show_screen('products');
                        }
                }
            });
            this.$('.set-customer').click(function(){
                self.gui.show_screen('clientlist');
            });
        }
    });
	
	var _super_PaymentScreenWidget = screens.PaymentScreenWidget;

    _super_PaymentScreenWidget = screens.PaymentScreenWidget.include({
		
		validate_order: function(force_validation) {
			if(self.pos.gui.has_popup()) return
				if (this.order_is_valid(force_validation)) {
					this.finalize_validation();
				}
			},

        payment_input: function(input) {
            var newbuf = this.gui.numpad_input(this.inputbuffer, input, {'firstinput': this.firstinput});
            
            this.firstinput = (newbuf.length === 0);

            // popup block inputs to prevent sneak editing.
            if (this.gui.has_popup()) {

				if(input == 'BACKSPACE'){
					$('#bank_reference').val($('#bank_reference').val().slice(0,$('#bank_reference').val().length-1))
					if($('#bank_reference').val().length<6) $('#confirm').hide()
					return
				}

				if("0123456789".indexOf(input) < 0) return

				if($('#bank_reference').val().length<6){
					$('#bank_reference').val($('#bank_reference').val()+input)
				}
				if($('#bank_reference').val().length==6) $('#confirm').show()
				else $('#confirm').hide()


                return;
            }

            if (newbuf !== this.inputbuffer) {
                this.inputbuffer = newbuf;
                var order = this.pos.get_order();
                if (order.selected_paymentline) {
                    var amount = this.inputbuffer;

                    if (this.inputbuffer !== "-") {
                        amount = field_utils.parse.float(this.inputbuffer);
                    }

                    order.selected_paymentline.set_amount(amount);
                    this.order_changes();
                    this.render_paymentlines();
                    this.$('.paymentline.selected .edit').text(this.format_currency_no_symbol(amount));
                }
            }
        },
    });




    var _super_order = models.Order;
    models.Order = models.Order.extend({


        initialize: function(attributes,options){
            _super_order.prototype.initialize.apply(this,arguments);
			this.x_factor_with_card=0
        },

        init_from_JSON: function (json){
            this.x_bank_reference = json.x_bank_reference;
			this.x_factor_with_card = json.x_factor_with_card
            _super_order.prototype.init_from_JSON.apply(this, arguments);

        },

        export_as_JSON: function (){

            var data = _super_order.prototype.export_as_JSON.apply(this, arguments);
            data.x_bank_reference = this.x_bank_reference;
			data.x_factor_with_card = this.x_factor_with_card;
            return data;
        },

        //Inherited functions
        add_product: function(product, options){
            this.remove_all_paymentlines();
            _super_order.prototype.add_product.apply(this, arguments);

        },
		
		set_client: function(client){
			_super_order.prototype.set_client.apply(this, arguments);
			var orderlines = this.get_orderlines();
			if(orderlines.length>0){
				this.x_factor_with_card = ((self.pos.get_order().get_due()*self.pos.config['extra_charge'])/self.pos.get_order().get_total_with_tax())
                for(var i = 0; i< orderlines.length; i++){
                    var new_price = orderlines[i].get_unit_display_price()*((this.x_factor_with_card/100)+1);
                    orderlines[i].set_unit_price(new_price);
                }
                }
		},

        add_paymentline: function(cashregister){
            if(cashregister.uso_terminal_smay && this.payment_exists(cashregister)==false){
            var orderlines = this.get_orderlines();
            if(orderlines.length>0){
				this.x_factor_with_card = ((self.pos.get_order().get_due()*self.pos.config['extra_charge'])/self.pos.get_order().get_total_with_tax())
                for(var i = 0; i< orderlines.length; i++){
                    var new_price = orderlines[i].get_unit_display_price()*((this.x_factor_with_card/100)+1);
                    orderlines[i].set_unit_price(new_price);
                }
                self.pos.gui.show_popup('BankReferencePopUp',{
                'amount': self.pos.get_order().get_total_with_tax()-self.pos.get_order().get_total_paid()
               })
               }
            }

            _super_order.prototype.add_paymentline.apply(this,arguments);
			
        },

        remove_paymentline: function(line){
            if(line.payment_method['uso_terminal_smay']){
                var orderlines = this.get_orderlines();
                for(var i = 0; i< orderlines.length; i++){
                    //var new_price = orderlines[i].get_unit_display_price()/((this.pos.config['extra_charge']/100)+1);
					var new_price = orderlines[i].get_unit_display_price()/((this.x_factor_with_card/100)+1);
                    orderlines[i].set_unit_price(new_price);
					
                }
				this.x_factor_with_card=0
                this.x_bank_reference=''
            }
            _super_order.prototype.remove_paymentline.apply(this, arguments);
        },

        remove_all_paymentlines: function(){
            var paymentlines = this.get_paymentlines();
            for(var i=0; i<paymentlines.length; i++){
                this.remove_paymentline(paymentlines[i]);
                i--;
            }
        },

    });

    var _super_orderline = models.Orderline;
    models.Orderline = models.Orderline.extend({
        set_quantity: function(quantity, keep_price){
           if(self.pos.get_order()) self.pos.get_order().remove_all_paymentlines();
            _super_orderline.prototype.set_quantity.apply(this,arguments);
        },
    });
});
