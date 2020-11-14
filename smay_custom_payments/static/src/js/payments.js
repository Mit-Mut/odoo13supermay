odoo.define('smay_custom_payments.smay_custom_payments', function(require){
    "use strict";

	var models = require('point_of_sale.models');

	var _super_order = models.Order;

	models.Order = models.Order.extend({

	    add_paymentline: function(payment_method) {
	        var method = payment_method['name'];
	        if(this.payment_exists(method)==false){
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
});


