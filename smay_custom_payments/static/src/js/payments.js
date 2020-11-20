odoo.define('smay_custom_payments.smay_custom_payments', function(require){
    "use strict";

	var models = require('point_of_sale.models');

	var _super_order = models.Order;
	var _super_paymentline = models.Paymentline

	models.Order = models.Order.extend({

	    add_paymentline: function(payment_method) {
	        var method = payment_method['name'];
	        console.log(this.payment_exists(method))
	        console.log(this.pos.get_order().get_due())
	        if(this.payment_exists(method)==false && this.pos.get_order().get_due()>0){
	            _super_order.prototype.add_paymentline.apply(this,arguments);
	        }
	    },

	    payment_exists:function(method){
	        var paymentlines = this.get_paymentlines();
	        if(!this.pos.config.multiple_payments && paymentlines.length>=1){
	            return true;
	        }
            for(var i=0; i<paymentlines.length ; i++){
                if(paymentlines[i].name==method){
                    return true;
                }
            }
            return false;
	    },

	});


    models.Paymentline = models.Paymentline.extend({

    set_amount: function(value){
    console.log(value)
    console.log(this)
    if(this.payment_method.is_cash_count)
        _super_paymentline.prototype.set_amount.apply(this,arguments)
    else if(this.pos.get_order().get_due()>0)
    _super_paymentline.prototype.set_amount.apply(this,arguments)
    },

    });
});


