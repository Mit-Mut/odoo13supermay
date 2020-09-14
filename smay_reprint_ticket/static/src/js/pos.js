odoo.define('smay_reprint_ticket.smay_reprint_ticket', function(require){
    "use strict";

    var chrome = require('point_of_sale.chrome');
    var gui = require('point_of_sale.gui');
    var popups = require('point_of_sale.popups');
    var models = require('point_of_sale.models');
    var rpc = require('web.rpc')
    var core = require('web.core');
    var QWeb = core.qweb;

    models.load_fields('res.users', ['pos_security_pin','sucursal_id']);

    var _super_orderline = models.Orderline;

    models.Orderline = models.Orderline.extend({
        initialize: function(attr,options){
            this.x_descuento =0.0;
            _super_orderline.prototype.initialize.apply(this,arguments);
        },

        init_from_JSON: function (json){
            this.x_descuento = json.x_descuento;
            _super_orderline.prototype.init_from_JSON.apply(this, arguments);

        },

        clone: function (){
            var data = _super_orderline.prototype.clone.apply(this, arguments)
            if(this.product.lst_price - this.get_unit_display_price()>0)
                data.this.x_descuento = this.product.lst_price - this.get_unit_display_price()
            else
                data.x_descuento=0
            return data
        },

        export_as_JSON: function (){
            var data = _super_orderline.prototype.export_as_JSON.apply(this, arguments)
            if(this.product.lst_price - this.get_unit_display_price()>0)
                data.x_descuento=(this.product.lst_price - this.get_unit_display_price())*this.quantity
            else
                data.x_descuento=0
            return data
        },

    });


    chrome.OrderSelectorWidget.include({
        renderElement: function(){
            var self = this;
            this._super();
            this.$('.smay_menu').click(function(){
                if(self.gui.get_current_screen()=='receipt'){
                    $('.button.next.highlight').click();
                }
                self.gui.show_popup('PopUpMenu');
            });
		},
	});


	gui.Gui = gui.Gui.extend({
        ask_password_smay: function(action) {
            var self = this;
            var _managers =[];
			console.log('action'+action)
			if(action=='Reporte de Arqueo/Cierre'){
				console.log('entro para imprimir cierre')
				for(var i=0; i<self.pos.users.length; i++){
                if(self.pos.users[i].role=='manager'){
                    _managers.push(self.pos.users[i].pos_security_pin);
                }
            }
			}
				
			else{
            for(var i=0; i<self.pos.users.length; i++){
                if(self.pos.users[i].is_manager && self.pos.users[i].sucursal_id[0]==self.pos.config.sucursal_id[0] ){
                    _managers.push(self.pos.users[i].pos_security_pin);
                }
            }
			}

            var ret = new $.Deferred();
                this.show_popup('password',{
                    'title': 'Contraseña',
                    confirm: function(pw) {
                        var manager_id = 0
                        for(var i=0; i<self.pos.users.length; i++){
                            if(self.pos.users[i].is_manager && self.pos.users[i].pos_security_pin==pw){
                                manager_id = self.pos.users[i].id
                            }
                        }

                        if(!_managers.includes(pw)){
                            self.show_popup('error','Contraseña incorrecta');
                            ret.reject();
                        } else {
                            rpc.query({
                                model : 'log.manager',
                                method: 'create',
                                args : [
                                    {
                                    sucursal_id:self.pos.config.sucursal_id[0],
                                    operacion:action,
                                    cajero_id:self.pos.get_cashier().user_id[0],
                                    manager_id : manager_id,
                                }],
                                timeout: 2000,
                            }).then(function(){
                                console.log('Creación exitosa de log - ' +new Date())
                            }).catch(function(){
                                console.log("FALLO EL LOG")
                                })
                            ret.resolve();
                        }
                    },
                });
            return ret;
        },
    });

	var ReprintTicketPopUp = popups.extend({
	    template:'ReprintTicketPopUp',

	    get_correct_datetime : function(date){
            var correct_datetime = new Date(date+' UTC').toString();
            var correct_date = date.substring(0,10);
            var correct_time = correct_datetime.substring(16,24);
            return correct_date.substring(8,10)+'/'+correct_date.substring(5,7)+'/'+correct_date.substring(0,4) +' '+correct_time;
	    },

	    show: function(options){
	        var self = this;
	        self._super(options);
	                rpc.query({
	                    model : 'pos.config',
	                    method: 'existe_conexion',
	                    args : [],
	                    timeout: 1000,
	                })
	                .then(function(){
                                    rpc.query({
                                        model:'pos.order',
                                        method: 'get_tickets_for_reprint',
                                        args: [],
                                        timeout: 3000,
                                    }).then(function(tickets){
                                        for(var i in tickets){
                                            var devolucion=''
                                            var cliente ='Público en General'
                                            //console.log(tickets)
                                             if(tickets[i].cliente) cliente=tickets[i].cliente

                                            //if(tickets[i].is_refund) devolucion='DEVOLUCIÓN'
                                            $("#tickets").append('<option value="'+tickets[i].id+'">'+'   '
                                            +tickets[i].pos_reference+'  -  '
                                            +self.get_correct_datetime(tickets[i].date_order)+ '  -  '+tickets[i].cashier+'  (  '
                                            +self.format_currency(tickets[i].amount_total,2)+'  )  -  '+cliente+'  -  '
                                            +devolucion+'  </option>');
                                        }
                                    }).catch(function(){
                                    });

                    }).catch(function(){
                        self.gui.show_popup('error',{
                            title: 'Sin conexión al servidor',
                            body: 'Por el momento no se puede obtener la información del sevidor. Intentalo más tarde',
                         });
                    });

            self.$('#accept').on('click',function(){
                    if($( "#tickets").children("option:selected").val()== undefined){
						self.pos.gui.show_popup('error',{
							'title':'Sin tickets que mostar',
							'body': 'No hay tickets disponibles para reimprimir',
						})
						return
                    }

                    rpc.query({
                        model: 'pos.order',
                        method: 'get_information_reprint',
                        args:[$( "#tickets").children("option:selected").val(),false],
                        }).then(function(data){
                            //self.gui.show_screen('receipt',{reprint:'true'})
                            var date_reprint = new Date()
                            var day = (date_reprint.getDate()>=10) ? date_reprint.getDate() : '0'+date_reprint.getDate()
                            var month  = ((parseInt(date_reprint.getMonth())+1)>=10) ? (parseInt(date_reprint.getMonth())+1) : '0'+(parseInt(date_reprint.getMonth())+1)
                            var hours =  (date_reprint.getHours()>=10)? date_reprint.getHours() : '0'+date_reprint.getHours()
                            var minutes = (date_reprint.getMinutes() >=10) ? date_reprint.getMinutes() : '0'+date_reprint.getMinutes()
                            var seconds = (date_reprint.getSeconds()>=10) ? date_reprint.getSeconds() : '0'+date_reprint.getSeconds()

                            var receipt = {
                                //head
                                logo : self.pos.company_logo.currentSrc,
                                company_name : self.pos.company.name,
                                rfc : self.pos.company.vat,
                                street : self.pos.company.street,
                                zip : self.pos.company.zip,
                                city : self.pos.company.city,
                                state : self.pos.company.state_id[1],
                                country : self.pos.company.country.name,
                                phone: self.pos.company.phone,

                                //body
                                order_name : data.pos_reference,
                                date_order: self.get_correct_datetime(data.date_order),
                                cashier : data.cashier,
                                client : data.partner? data.partner:'Público en General',
                                header : self.pos.config.recepit_header,
                                orderlines : data.orderlines,
                                subtotal : data.subtotal,
                                taxes : data.taxes,
                                total: data.total,
                                paymentlines : data.payments,
                                change_amount : data.change_amount,
                                qty_products : data.qty_products,
                                footer: self.pos.config.receipt_footer,
								x_bank_reference : data.x_bank_reference,

                                date_reprint : day+'/'+month+'/'+date_reprint.getFullYear()+'  '+hours+':'+minutes+':'+seconds

                            }

                            self.pos.config.iface_print_auto  = false;
                            self.gui.show_screen('receipt',{reprint:'true'})
                            $('.pos-receipt').html(QWeb.render('ReprintPosTicket' ,{widget:self,receipt:receipt}));
                            this.print()
                            console.log(this)

                        }).catch(function(){
                    });
            });

            self.$('#cancel').on('click',function(){
                self.gui.close_popup();
            });
	    },
	});

	gui.define_popup({name:'ReprintTicketPopUp',widget: ReprintTicketPopUp});


    var PopUpMenu = popups.extend({
		template: 'PopUpMenu',

		show: function(options){
			var self = this;
			self._super(options);

			$('.gridView-toolbar.reprintButton').on('click',function(){
				//self.gui.show_popup('ReprintTicketPopUp');
				var reprint_pass = self.gui.ask_password_smay('reimpresión de ticket');
                reprint_pass.done(function(){
                    self.gui.show_popup('ReprintTicketPopUp');
                });
			});

			$('.button.close').on('click',function(){
				self.gui.close_popup();
			});
		}
	});
	gui.define_popup({name:'PopUpMenu',widget: PopUpMenu});

	return{
        PopUpMenu: PopUpMenu,
        ReprintTicketPopUp:ReprintTicketPopUp,
    };

 });
