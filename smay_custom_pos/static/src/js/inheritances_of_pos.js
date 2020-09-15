odoo.define('smay_custom_pos.smay_custom_pos', function(require){
    "use strict";

	var gui = require('point_of_sale.gui');
	var session = require('web.session');
	var core = require('web.core');
	var _t = core._t;
	var models = require('point_of_sale.models');

	var Gui = gui.Gui;
    Gui.include({
		_close: function() {
			var self = this;
			this.chrome.loading_show();
			this.chrome.loading_message(_t('Closing ...'));
			this.pos.push_order().then(function(){
				var url = "/web#id="+ self.pos.pos_session.id +"&view_type=form&model=pos.session";
				console.log(url)
				window.location = session.debug ? $.param.querystring(url, {debug: session.debug}) : url;
			});
		},
    });


    var _super_product = models.Product;
	models.Product = models.Product.extend({

        get_price: function(pricelist, quantity){
            var self= this;
            var price = self._super(this, arguments);
            return Math.round(price*10)/10
        },
    });
});
