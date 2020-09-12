odoo.define('pos_cash_alert.pos_cash_alert', function (require) {
"use strict";

	var pos_model = require('point_of_sale.models');
	var popup_widget = require('point_of_sale.popups');
	var screens = require('point_of_sale.screens');
	var gui = require('point_of_sale.gui');
	var reprint_ticket = require('smay_reprint_ticket.smay_reprint_ticket')
	var rpc = require('web.rpc');
	var core = require('web.core');
	var QWeb = core.qweb;

	var SuperReceiptScreenWidget = screens.ProductScreenWidget.prototype;

    pos_model.load_fields('pos.session',['cash_register_difference','cash_register_balance_start']);

	var CashOutPopupWidget = popup_widget.extend({
		template: 'CashOutPopupWidget',

		calculate_retirement_amount:function(){
            var total_amount=0;

            if($('#un_peso').val()!= 0 && $('#un_peso').val()!= '' ){
                $('#un_peso').val(Math.abs($('#un_peso').val()));
                total_amount = parseFloat(total_amount)+parseFloat($('#un_peso').val())* 1;
            }else{
                $('#un_peso').val(0);
            }

            if($('#diez_pesos').val()!= 0 && $('#diez_pesos').val()!= '' ){
                $('#diez_pesos').val(Math.abs($('#diez_pesos').val()));
                total_amount = parseFloat(total_amount)+parseFloat($('#diez_pesos').val())*10;
            }else{
                $('#diez_pesos').val(0);
            }

            if($('#veinte_pesos').val()!= 0 && $('#veinte_pesos').val()!= '' ){
                $('#veinte_pesos').val(Math.abs($('#veinte_pesos').val()));
                total_amount = parseFloat(total_amount)+parseFloat($('#veinte_pesos').val())* 20;
            }else{
                $('#veinte_pesos').val(0);
            }

            if($('#cincuenta_pesos').val()!= 0 && $('#cincuenta_pesos').val()!= '' ){
                $('#cincuenta_pesos').val(Math.abs($('#cincuenta_pesos').val()));
                total_amount = total_amount+$('#cincuenta_pesos').val()*50;
            }else{
                $('#cincuenta_pesos').val(0);
            }

            if($('#cien_pesos').val()!= 0 && $('#cien_pesos').val()!= '' ){
                $('#cien_pesos').val(Math.abs($('#cien_pesos').val()));
                total_amount = total_amount+$('#cien_pesos').val()*100;
            }else{
                $('#cien_pesos').val(0);
            }

            if($('#doscientos_pesos').val()!= 0 && $('#doscientos_pesos').val()!= '' ){
                $('#doscientos_pesos').val(Math.abs($('#doscientos_pesos').val()));
                total_amount = total_amount+$('#doscientos_pesos').val()*200;
            }else{
                $('#doscientos_pesos').val(0);
            }

            if($('#quinientos_pesos').val()!= 0 && $('#quinientos_pesos').val()!= '' ){
                $('#quinientos_pesos').val(Math.abs($('#quinientos_pesos').val()));
                total_amount =total_amount+ $('#quinientos_pesos').val()*500;
            }else{
                $('#quinientos_pesos').val(0);
            }

            if($('#mil_pesos').val()!= 0 && $('#mil_pesos').val()!= '' ){
                $('#mil_pesos').val(Math.abs($('#mil_pesos').val()));
                total_amount =total_amount+ $('#mil_pesos').val()*1000;
            }else{
                $('#mil_pesos').val(0);
            }

            $('#amount_out').val(total_amount);
		},


	    number_format:function(amount, decimals) {
            amount += ''; // por si pasan un numero en vez de un string
            amount = parseFloat(amount.replace(/[^0-9\.]/g, '')); // elimino cualquier cosa que no sea numero o punto
            decimals = decimals || 0; // por si la variable no fue fue pasada

            // si no es un numero o es igual a cero retorno el mismo cero
            if (isNaN(amount) || amount === 0)
                return parseFloat(0).toFixed(decimals);

            // si es mayor o menor que cero retorno el valor formateado como numero
            amount = '' + amount.toFixed(decimals);

            var amount_parts = amount.split('.'),
            regexp = /(\d+)(\d{3})/;

            while (regexp.test(amount_parts[0]))
                amount_parts[0] = amount_parts[0].replace(regexp, '$1' + ',' + '$2');

            return amount_parts.join('.');
        },

		show: function(options){
			var self = this;
			self._super(options);
			$('#put_in_out_error').hide();
			$('#veinte_pesos').focus(function(){
			    this.select();
			});
			//$('#amount_out').focus();
			//$('#amount_out').val(self.pos.config.cash_withdraw);
			$('#amount_out').val(0);
			$("#amount_out").attr('readonly','readonly');

			$('#un_peso').on('change',function(){
			    self.calculate_retirement_amount();
			});

			$('#cinco_pesos').on('change',function(){
				self.calculate_retirement_amount();
			});

			$('#diez_pesos').on('change',function(){
				self.calculate_retirement_amount();
			});

			$('#veinte_pesos').on('change',function(){
				self.calculate_retirement_amount();
			});

			$('#cincuenta_pesos').on('change',function(){
				self.calculate_retirement_amount();
			});

			$('#cien_pesos').on('change',function(){
				self.calculate_retirement_amount();
			});

			$('#doscientos_pesos').on('change',function(){
				self.calculate_retirement_amount();
			});

			$('#quinientos_pesos').on('change',function(){
				self.calculate_retirement_amount();
			});

			$('#mil_pesos').on('change',function(){
				self.calculate_retirement_amount();
			});

			$('.button.cash_apply').on('click',function(){
				$('.button.cash_apply').hide()
			    var denominations = {};
			    var text_denominations = [];

			    $('#denominacion_billetes tr td input').each(function(){
			        denominations[$(this).attr('name')] = self.number_format(parseFloat($(this).val()),2).replace(/,/g,'');
			    });

			    $('#denominacion_billetes tr td input').each(function(){
                    var denominations2 = {
                                'denomination': '$ '+ self.number_format($(this).attr('name'),2),
                                'qty': self.number_format(parseFloat($(this).val()),2),
                                'amount': '$ '+ self.number_format($(this).attr('name')* $(this).val(),2),
                                }
                    text_denominations.push(denominations2);
			    });

				var amount_out = parseFloat($('#amount_out').val());
				if (amount_out <= 0  || isNaN(amount_out)){
					$("#amount_out").css("background-color","burlywood");
					setTimeout(function(){
						$("#amount_out").css("background-color","");
					},100);
					setTimeout(function(){
						$("#amount_out").css("background-color","burlywood");
					},200);
					setTimeout(function(){
						$("#amount_out").css("background-color","");
					},300);
					setTimeout(function(){
						$("#amount_out").css("background-color","burlywood");
					},400);
					setTimeout(function(){
						$("#amount_out").css("background-color","");
					},500);
					$('.button.cash_apply').show()
					return;
				}
				else if ($("#reason_out").val() == ''){
					$("#reason_out").css("background-color","burlywood");
					setTimeout(function(){
						$("#reason_out").css("background-color","");
					},100);
					setTimeout(function(){
						$("#reason_out").css("background-color","burlywood");
					},200);
					setTimeout(function(){
						$("#reason_out").css("background-color","");
					},300);
					setTimeout(function(){
						$("#reason_out").css("background-color","burlywood");
					},400);
					setTimeout(function(){
						$("#reason_out").css("background-color","");
					},500);
					$('.button.cash_apply').show()
					return;
				}
				else{
					var result = {}
					$('#amount_out').val(0)
					var amount = parseFloat($('#amount_out').val());
					//var reason = "Reason:" + ($("#reason_out").val());
					var reason =  ($("#reason_out").val());

					rpc.query({
					    model : 'pos.config',
					    method: 'existe_conexion',
					    args:[],
					}).then(function(resp){
                        rpc.query({
                            model: 'pos.session',
                            method: 'set_cash_box_out_value',
                            args: [
                                self.pos.pos_session.id,{
                                'amount': amount_out,//12,//amount,
                                'reason': reason,
                                'ref' : self.pos.pos_session.name,
                                'comment': ($("#comment").val()),
                                'denominations': denominations,
                                'sucursal_id': self.pos.config.sucursal_id[0],
                                'check_cash': true
                            }]
                        }).then(function(last_id_out){

                            if(last_id_out==-1){
                                self.gui.show_popup('error', {
                                    title: 'No se realizó el Retiro.',
                                    body: 'El monto del retiro ($'+ self.number_format(parseFloat(amount_out),2) +'), excede a lo que se tiene en caja.',
                                });
                                $('.popup.popup-error').css({'height':'200px','width':'400px'})
						        return
                            }
							
							self.gui.show_popup('success',{
								message: 'El retiro de '+ self.number_format(parseFloat(amount_out),2) +' fue exitoso'
							})
							
							setTimeout(function(){
								var date    = new Date();
								var company = self.pos.company;
								var receipt = {
									NameSession: self.pos.pos_session.name,
									cashier: self.pos.get('cashier').name || self.pos.user.name,
									moneyOut: '$ '+self.number_format(parseFloat(amount_out),2),//amount_out,//parseFloat($('#amount_out').val()),
									reason: $("#reason_out").val() ? $("#reason_out").val().toUpperCase():'retiro',
									comment: ($("#comment").val()),
									//last_id_out: last_id_out,
									last_id_out: last_id_out,
									precision: {
										price: 2,
										yeaey: 2,
										quantity: 3,
									},
									date: {
										year: date.getFullYear(),
										month: date.getMonth(),
										date: date.getDate(),       // day of the month
										day: date.getDay(),         // day of the week
										hour: date.getHours(),
										minute: date.getMinutes() ,
										isostring: date.toISOString(),
										localestring: date.toLocaleString(),
									},
									company:{
										name: company.name,
										phone: company.phone,
										email: company.email,
										country: company.country.name,
										website: company.website,
										logo: self.pos.company_logo_base64,
									},
									//denominations: denominations,
									denominations: text_denominations,
									url_id: self.pos.attributes.origin+"/report/barcode/Code128/"+last_id_out,
								};

								var env = {
									widget:  self,
									receipt: receipt
								};

								if(self.gui.get_current_screen() != 'receipt')
									self.gui.show_screen('receipt',{'retirement': true});
								var receiptFinal = QWeb.render('XmlReciboDeRetiro',env);
								$('.pos-receipt').html(receiptFinal);
							}, 1500)
					    }).catch(function(unused, event){
						    self.gui.show_popup('error', {
							    title: 'No se registro el retiro en el sistema.',
							    body: 'Por favor revisa la conexión a internet.',
						    });
						    event.preventDefault();
					    });
					}).catch(function(resp){
                        self.gui.show_popup('error', {
            				title:'Retiro de Efectivo.',
			            	body:'No hay conexiòn al servidor, por favor revisa la conexión a internet.',
						});
					});
					self.gui.close_popup();
				}
			});
		}
	});
	gui.define_popup({name:'cash_out_popup',widget: CashOutPopupWidget});

	var SuccessPopopWidget = popup_widget.extend({
		template: 'SuccessPopopWidget',
		events:{
			'click .button.cancel': 'click_cancel'
		},

		show: function(options){
			var self = this;
			self._super(options)
			this.options = options;
			this.$('.cash_out_status').show();
            this.$('.cash_out_status').removeClass('withdraw_done');
			this.$('.show_tick').hide();
			setTimeout(function(){
				$('.cash_out_status').addClass('withdraw_done');
  				$('.show_tick').show();
				$('.cash_out_status').css({'border-color':'#5cb85c'})
			},500)
			setTimeout(function(){
				self.pos.gui.close_popup();
			},1500)
		},
	});

	gui.define_popup({
		name: 'success',
		widget: SuccessPopopWidget
	});

	var CashPopupWidget = popup_widget.extend({
		template:'CashPopupWidget',
		show: function(options){
			this._super(options);
			var self = this;
			var difference_amount = self.chrome.screens.scale.format_currency(Math.abs(self.pos.cash_register_difference));
			//var threshold_amount = self.chrome.screens.scale.format_currency(self.pos.config.cash_threshold);
			var withdraw_amount = self.chrome.screens.scale.format_currency(self.pos.config.cash_withdraw);
			//self.$("#cash_message").text('Cash drawer content is '+difference_amount+', maximum amount is '+threshold_amount+', please put '+withdraw_amount+' in safebox');
			self.$("#cash_message").text('Es necesario que realices un retiro de efectivo, tu caja excedio los  '+withdraw_amount+ '  permitidos.');
			self.$('#now').on('click',function(){
				//self.gui.show_popup('cash_out_popup');

				///Revisa que no haya facturas sin timbrar

		        rpc.query({
                    model:'pos.config',
                    method: 'existe_conexion',
                    args:[],

                },{
                    timeout:1000,
                    shadow:true
                }).then(function(resp){

                    rpc.query({
                        model:'pos.session',
                        method: 'get_unsigned_invoices',
                        args:[self.pos.pos_session.id],

                    },{
                        timeout:5000,
                        shadow:true
                    }).then(function(resp){
                        //console.log(resp)
                        var orders ='\n'
                        var elements =0
                        for(var r in resp){
                            console.log(r)
                            orders+=r+'.  '
                            elements++
                        }
                        orders+='\n'

                      if(elements>0 )
                          self.gui.show_popup('error',{
                              title:'Facturas sin timbrar',
                              body:'Hay facturas que no fueron timbradas exitosamente.\n Para realizar el retiro es necesario timbrarlas:  '+ orders +'\n.'
                          })
                    }).catch(function(){
                      //console.log('fallo la respuesta del server')
                    })



                }).catch(function(){
                    self.gui.show_popup('error',{
                        title:'Sin conexión',
                        body:'No hay conexión con el servidor, contacta al administrador del sistema.'
                    })
                })

              ////
				var retirement_pass = self.gui.ask_password_smay('retiro');
				$('.button.cancel').hide();

                retirement_pass.done(function(){
                    self.gui.show_popup('cash_out_popup');
                }).catch(function(unused,event){
                setTimeout(function(){
					    self.gui.show_popup('cash_popup');},1500);
					});
			});
		}
	});
	gui.define_popup({name:'cash_popup', widget: CashPopupWidget});

	screens.ProductScreenWidget.include({
		show: function(){
			this._super();
			var self = this;

			if(self.pos.config.cash_withdraw != 0){
				setTimeout(function(){
					//new Model('pos.session').call('get_cash_register_difference',[self.pos.pos_session.id])
					console.log('entroaosdaoidjaoisdoasid')
					rpc.query({
					    model:'pos.session',
					    //method: 'get_cash_register_difference',
					    method:'get_cash_register_total_entry_encoding',
					    args: [self.pos.pos_session.id]
					//}).then(function(cash_register_difference){
					    }).then(function(get_cash_register_total_entry_encoding){
					    console.log(get_cash_register_total_entry_encoding)
						/*if(cash_register_difference > 0) return
					    self.pos.cash_register_difference = cash_register_difference;
						if(self.pos.config.cash_withdraw - Math.abs(parseFloat(cash_register_difference,10)+parseFloat(self.pos.config.fondo_caja,10))<=0)
							if(self.gui!=null && self.pos.get_order().get_orderlines().length == 0)
						self.gui.show_popup('cash_popup',{});*/
					}).catch(function(unused,event){
					    event.preventDefault();
					});
				}, 1000);
			}
		}
	});

    reprint_ticket.PopUpMenu.include({
        show: function(options){
            var self = this;
			self._super(options);
			$('.gridView-toolbar.retirementButton').on('click',function(){

			    			    //Revisa que no haya facturas sin timbrar

			    rpc.query({
                    model:'pos.config',
                    method: 'existe_conexion',
                    args:[],
                },{
                    timeout:1000,
                    shadow:true
                }).then(function(resp){

                    rpc.query({
                        model:'pos.session',
                        method: 'get_unsigned_invoices',
                        args:[self.pos.pos_session.id],
                    },{
                        timeout:5000,
                        shadow:true
                    }).then(function(resp){
                        //console.log(resp)
                        var orders ='\n'
                        var elements =0
                        for(var r in resp){
                            //console.log(r)
                            orders+=r+'.  '
                            elements++
                        }
                        orders+='\n'

                        if(elements>0 )
                            self.gui.show_popup('error',{
                                title:'Facturas sin timbrar',
                                body:'Hay facturas que no fueron timbradas exitosamente.\n Para realizar el retiro es necesario timbrarlas:  '+ orders +'\n.'
                            })
                    }).catch(function(){
                        //console.log('fallo la respuesta del server')
                    })
                }).catch(function(){
                    self.gui.show_popup('error',{
                        title:'Sin conexión',
                        body:'No hay conexión con el servidor, contacta al administrador del sistema.'
                    })
                })

                var refund_pass = self.gui.ask_password_smay('retiro de efectivo');
                refund_pass.done(function(){
                    self.gui.show_popup('cash_out_popup');
                });
			});
        }
    });
});
