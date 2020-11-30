odoo.define('smay_close_pos.smay_close_pos', function(require){
    "use strict";

    var gui = require('point_of_sale.gui');
    var popups = require('point_of_sale.popups');
    var screens = require('point_of_sale.screens');
    var pos_model = require('point_of_sale.models');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var QWeb = core.qweb;
    var ActionManager = require('web.ActionManager');

    pos_model.load_fields('pos.session',['cash_register_balance_end_real','cash_register_total_entry_encoding']);

    var reprint_ticket = require('smay_reprint_ticket.smay_reprint_ticket');

    var _super_order = pos_model.Order;
    pos_model.Order = pos_model.Order.extend({

        add_product: function(product, options){
            _super_order.prototype.add_product.apply(this, arguments);

            if(!self.pos.config.es_checador_precios){
                rpc.query({
                    model:'pos.session',
                    method:'get_session_start_at',
                    args:[self.pos.pos_session.id],
                    timeout:500,
                }).then(function(resp){
                    var hora_apertura=resp.substr(5,2)+'/'+resp.substr(8,2)+'/'+resp.substr(0,4)+' '+resp.substr(11,8)+' UTC'
                    var hora_apertura_local = new Date(hora_apertura)
                    var fecha_actual = new Date()
                    if(fecha_actual.getDate()!=hora_apertura_local.getDate() || fecha_actual.getMonth()+1!=hora_apertura_local.getMonth()+1||fecha_actual.getFullYear()!=hora_apertura_local.getFullYear()){
                        self.pos.get_order().remove_all_paymentlines()
                        for(var i= 0; i<self.pos.get_order().get_orderlines().length; i++){
                            self.pos.get_order().remove_orderline(self.pos.get_order().get_orderlines()[i])
                                i--
                        }

                        self.pos.gui.show_popup('error',{
                            title: 'Error en Sesión',
                            body:'Debes de cerrar tu sessión porque no fue inicializada hoy.'
                        })
                        $('.popup-error').height(300)

                    }
                }).catch(function(){
                    var session_start_at = self.pos.pos_session.start_at
                    var hora_apertura=session_start_at.substr(5,2)+'/'+session_start_at.substr(8,2)+'/'+session_start_at.substr(0,4)+' '+session_start_at.substr(11,8)+' UTC'
                    var hora_apertura_local = new Date(hora_apertura)
                    var fecha_actual = new Date()
                    if(fecha_actual.getDate()!= hora_apertura_local.getDate() ||
                        fecha_actual.getMonth()+1!=hora_apertura_local.getMonth()+1||
                        fecha_actual.getFullYear()!=hora_apertura_local.getFullYear()){

                        self.pos.get_order().remove_all_paymentlines()
                        for(var i= 0; i<self.pos.get_order().get_orderlines().length; i++){
                            self.pos.get_order().remove_orderline(self.pos.get_order().get_orderlines()[i])
                            i--
                        }

                        self.pos.gui.show_popup('error',{
                            title: 'Error en Sesiòn',
                            body:'Debes de cerrar tu session.'
                        })

                        $('.popup-error').height(300)
                    }
                });
            }
        },
    });

    var ConfirmationClosePopupWidget = popups.extend({
        template : 'ConfirmationClosePopupWidget',

        show: function(options){
            var self= this;
            self._super(options);

            $('.button.acceptConfirmationClose').on('click',function(){
                $('.button.acceptConfirmationClose').hide()
                self.gui.close_popup();
				
				
				self.pos.gui.show_popup('alert',{
                        'title': 'Proceso de Cierre',
                        'body': 'El proceso de cierre esta en ejecución, espera un momento .'
                        })
                setTimeout(function(){
                    $('.popup.popup-alert').css('height','200px');
                    $('.footer').hide()
                ,1000})
				
				var timeout_close = (self.pos.get_order().sequence_number+20)*5*1000
				
				console.log('Inicio de cierre')
				console.log(Date())
				console.log('ordernes a cerrar: '+self.pos.get_order().sequence_number)
				console.log('Timeout:')
				console.log(timeout_close)
				
                rpc.query({
                    model:'pos.session',
                    method:'action_pos_session_closing_control_from_pos',
                    args:[self.pos.pos_session.id],
						timeout:60000,
                        shadow: true,
                    }).then(function(resp){
        				if(resp==-1){
                            self.pos.gui.show_popup('error','No se realizo el cierre, la diferencia del efectivo es mayor a la permitida.')
                            return
				        }

				        if(resp==-2){
				            //self.pos.gui.show_popup('error','Existen ventas con cliente asignado y sin facturar. Para poder cerrar la caja debes facturar las ordenes.')
				            self.pos.gui.show_popup('error','Existen ventas con factura asignada pero no estan timbradas. Para poder cerrar la caja debes de timbrar las facturas.')
                            return
				        }

                        $('.next').hide();
                        $('.header-button.smay_menu').hide();
                        $('.order-button.square.neworder-button').hide();
                        $('.order-button.square.deleteorder-button').hide();
                        var pos_session_id = [self.pos.pos_session.id];
						
						if(self.pos.config.enable_x_report) {
                            //var pos_session_id = [self.pos.pos_session.id]
							
							console.log('exito -  recibio respuesta')
							console.log(Date())

							setTimeout(function(){
								self.pos.gui.show_popup('alert',{
									'title': 'Cierre de Caja',
									'body': 'Caja cerrada exitosamente.'
								})
							$('.popup.popup-alert').css('height','200px')
							//$('.footer').hide()
							,10000})
							
			                self.pos.chrome.do_action('aces_pos_x_report.report_pos_sales_pdf_front',{additional_context:{
				                active_ids: [self.pos.pos_session.id],//pos_session_id,
			                }}).catch(function(){
								self.pos.gui.show_popup('error','No se pudo generar el reporte de cierre');
								});
                        }else{show_screen
                            self.pos.gui.show_popup('error', 'No esta habilitado en la configuración del punto de venta para imprimir el reporte');
                        }
                    }).catch(function(){
                    setTimeout(function(){
								self.pos.gui.show_popup('error',{
									'title': 'Cierre de Caja',
									'body': 'No se recibio respuesta del cierre en los '+timeout_close/1000+' segundos configurados.'
								})
							$('.popup.popup-error').css('height','200px')
							//$('.footer').hide()
							,10000})
							console.log('fail - no recibio respuesta')
							console.log(Date())

							$('.next').hide();
                            $('.header-button.smay_menu').hide();
                            $('.order-button.square.neworder-button').hide();
                            $('.order-button.square.deleteorder-button').hide();
                    });
            });

            $('.button.cancelConfirmationClose').on('click',function(){
                self.gui.close_popup()
            });
        },

    });

    gui.define_popup({name:'ConfirmationClosePopupWidget',widget: ConfirmationClosePopupWidget});

    var withdrawFundCashPopupWidget = popups.extend({
        template : 'withdrawFundCashPopupWidget',

        calculate_retirement_amount_fund:function(){
            var total_amount=0;
			
			if($('#un_peso_fund').val()!= 0 && $('#un_peso_fund').val()!= '' ){
                $('#un_peso_fund').val(Math.abs($('#un_peso_fund').val()));
                total_amount = parseFloat(total_amount)+parseFloat($('#un_peso_fund').val())*1;
            }else{
                $('#un_peso_fund').val(0);
            }

            if($('#diez_pesos_fund').val()!= 0 && $('#diez_pesos_fund').val()!= '' ){
                $('#diez_pesos_fund').val(Math.abs($('#diez_pesos_fund').val()));
                total_amount = parseFloat(total_amount)+parseFloat($('#diez_pesos_fund').val())* 10;
            }else{
                $('#diez_pesos_fund').val(0);
            }

            if($('#veinte_pesos_fund').val()!= 0 && $('#veinte_pesos_fund').val()!= '' ){
                $('#veinte_pesos_fund').val(Math.abs($('#veinte_pesos_fund').val()));
                total_amount = parseFloat(total_amount)+parseFloat($('#veinte_pesos_fund').val())* 20;
            }else{
                $('#veinte_pesos_fund').val(0);
            }

            if($('#cincuenta_pesos_fund').val()!= 0 && $('#cincuenta_pesos_fund').val()!= '' ){
                $('#cincuenta_pesos_fund').val(Math.abs($('#cincuenta_pesos_fund').val()));
                total_amount = parseFloat(total_amount)+parseFloat($('#cincuenta_pesos_fund').val())* 50;
            }else{
                $('#cincuenta_pesos_fund').val(0);
            }

            if($('#cien_pesos_fund').val()!= 0 && $('#cien_pesos_fund').val()!= '' ){
                $('#cien_pesos_fund').val(Math.abs($('#cien_pesos_fund').val()));
                total_amount = parseFloat(total_amount)+parseFloat($('#cien_pesos_fund').val())* 100;
            }else{
                $('#cien_pesos_fund').val(0);
            }

            if($('#doscientos_pesos_fund').val()!= 0 && $('#doscientos_pesos_fund').val()!= '' ){
                $('#doscientos_pesos_fund').val(Math.abs($('#doscientos_pesos_fund').val()));
                total_amount = parseFloat(total_amount)+parseFloat($('#doscientos_pesos_fund').val())* 200;
            }else{
                $('#doscientos_pesos_fund').val(0);
            }

            if($('#quinientos_pesos_fund').val()!= 0 && $('#quinientos_pesos_fund').val()!= '' ){
                $('#quinientos_pesos_fund').val(Math.abs($('#quinientos_pesos_fund').val()));
                total_amount = parseFloat(total_amount)+parseFloat($('#quinientos_pesos_fund').val())* 500;
            }else{
                $('#quinientos_pesos_fund').val(0);
            }

            /*if($('#mil_pesos_fund').val()!= 0 && $('#mil_pesos_fund').val()!= '' ){
                $('#mil_pesos_fund').val(Math.abs($('#mil_pesos_fund').val()));
                total_amount = parseFloat(total_amount)+parseFloat($('#mil_pesos_fund').val())* 1000;
            }else{
                $('#mil_pesos_fund').val(0);
            }*/

            $('#amount_fund').val(total_amount);
        },

        show: function(options){
            var self= this;
            self._super(options);

            $('#un_peso_fund').focus(function(){
                this.select();
            });

            $('#un_peso_fund').focus();
			$('#amount_fund').val(0);
			$("#amount_fund").attr('readonly','readonly');

			$('#un_peso_fund').on('change',function(){
			    self.calculate_retirement_amount_fund();
			});
			
			$('#diez_pesos_fund').on('change',function(){
			    self.calculate_retirement_amount_fund();
			});

			$('#veinte_pesos_fund').on('change',function(){
			    self.calculate_retirement_amount_fund();
			});

			$('#cincuenta_pesos_fund').on('change',function(){
			    self.calculate_retirement_amount_fund();
			});

			$('#cien_pesos_fund').on('change',function(){
			    self.calculate_retirement_amount_fund();
			});

			$('#doscientos_pesos_fund').on('change',function(){
			    self.calculate_retirement_amount_fund();
			});

			$('#quinientos_pesos_fund').on('change',function(){
			    self.calculate_retirement_amount_fund();
			});

			$('#mil_pesos_fund').on('change',function(){
			    self.calculate_retirement_amount_fund();
			});

			$('.button.acceptwidthdrawfund').on('click',function(){
				$('.button.acceptwidthdrawfund').hide()
			    var amount_fund = parseFloat($('#amount_fund').val());
			    if (amount_fund <= 0  || isNaN(amount_fund) || amount_fund != options['difference_fund'] ){
					$("#amount_fund").css("background-color","burlywood");

					setTimeout(function(){
						$("#amount_fund").css("background-color","");
					},100);

					setTimeout(function(){
						$("#amount_fund").css("background-color","burlywood");
					},200);

					setTimeout(function(){
						$("#amount_fund").css("background-color","");
					},300);

					setTimeout(function(){
						$("#amount_fund").css("background-color","burlywood");
					},400);

					setTimeout(function(){
						$("#amount_fund").css("background-color","");
					},500);
					$('.button.acceptwidthdrawfund').show()
					return;
				}else{
				    var denominations = {};
				    var denomin = [];

			        $('#denominacion_billetes_fund tr td input').each(function(){
			            if ($(this).attr('name') != 'amount_fund'){
			                denominations = {};
                            denominations['coin_value'] = parseFloat($(this).attr('name'));
                            denominations['number'] = parseFloat($(this).val());
                            denomin.push(denominations);
			            }
			        });

                    self.gui.close_popup();
			
		
                    rpc.query({
                        model:'pos.session',
                        method:'get_session_state',
                        args:[self.pos.pos_session.id],
                    },{
                        timeout:5000,
                        shadow:true
                    }).then(function(state){
                        if(state!='closed'){
                            rpc.query({
                                model:'account.bank.statement.cashbox',
                                method: 'return_session_fund',
                                args: [self.pos.pos_session.id,denomin],
                            },{
                                timeout: 5000,
                                shadow:true,
                            }).then(function(response){
                                self.pos.pos_session.cash_register_balance_end_real +=  parseFloat($("#amount_fund").val());
                                self.gui.show_popup('CloseCashPopupWidget');
                            }).catch(function(){
                                self.gui('error',{
                                    title: 'Retiro de fondo FALLIDO.',
                                    body: 'No se realizó el retiro del fondo exitosamente. Intenta de nuevo.',
                                });
                            });
                        }else{
                            var pos_session_id = [self.pos.pos_session.id]

                            self.pos.chrome.do_action('aces_pos_x_report.report_pos_sales_pdf_front',{additional_context:{
                                active_ids:pos_session_id,
                            }}).catch(function(){
                                self.pos.show_popup('error','no se generó en reporte. (0001)')
                            })
                        }
		            }).catch(function(){
			            self.pos.gui.show_popup('error','NO existe conexion con el servidor (0002)')
		            })
				}
			});
        },
    });

    gui.define_popup({name:'withdrawFundCashPopupWidget',widget: withdrawFundCashPopupWidget});

    var CloseCashPopupWidget = popups.extend({
        template : 'CloseCashPopupWidget',

        calculate_retirement_amount_close:function(){
            var total_amount=0;

            if($('#un_peso_close').val()!= 0 && $('#un_peso_close').val()!= '' ){
                $('#un_peso_close').val(Math.abs($('#un_peso_close').val()));
                total_amount = parseFloat(total_amount)+parseFloat($('#un_peso_close').val())* 1;
            }else{
                $('#un_peso_close').val(0);
            }

            /*if($('#dos_pesos_close').val()!= 0 && $('#dos_pesos_close').val()!= '' ){
                $('#dos_pesos_close').val(Math.abs($('#dos_pesos_close').val()));
                total_amount = parseFloat(total_amount)+parseFloat($('#dos_pesos_close').val())* 2;
            }else{
                $('#dos_pesos_close').val(0);
            }

            if($('#cinco_pesos_close').val()!= 0 && $('#cinco_pesos_close').val()!= '' ){
                $('#cinco_pesos_close').val(Math.abs($('#cinco_pesos_close').val()));
                total_amount = parseFloat(total_amount)+parseFloat($('#cinco_pesos_close').val())* 5;
            }else{
                $('#cinco_pesos_close').val(0);
            }*/

            if($('#diez_pesos_close').val()!= 0 && $('#diez_pesos_close').val()!= '' ){
                $('#diez_pesos_close').val(Math.abs($('#diez_pesos_close').val()));
                total_amount = parseFloat(total_amount)+parseFloat($('#diez_pesos_close').val())* 10;
            }else{
                $('#diez_pesos_close').val(0);
            }

            if($('#veinte_pesos_close').val()!= 0 && $('#veinte_pesos_close').val()!= '' ){
                $('#veinte_pesos_close').val(Math.abs($('#veinte_pesos_close').val()));
                total_amount = parseFloat(total_amount)+parseFloat($('#veinte_pesos_close').val())* 20;
            }else{
                $('#veinte_pesos_close').val(0);
            }

            if($('#cincuenta_pesos_close').val()!= 0 && $('#cincuenta_pesos_close').val()!= '' ){
                $('#cincuenta_pesos_close').val(Math.abs($('#cincuenta_pesos_close').val()));
                total_amount = parseFloat(total_amount)+parseFloat($('#cincuenta_pesos_close').val())* 50;
            }else{
                $('#cincuenta_pesos_close').val(0);
            }

            if($('#cien_pesos_close').val()!= 0 && $('#cien_pesos_close').val()!= '' ){
                $('#cien_pesos_close').val(Math.abs($('#cien_pesos_close').val()));
                total_amount = parseFloat(total_amount)+parseFloat($('#cien_pesos_close').val())* 100;
            }else{
                $('#cien_pesos_close').val(0);
            }

            if($('#doscientos_pesos_close').val()!= 0 && $('#doscientos_pesos_close').val()!= '' ){
                $('#doscientos_pesos_close').val(Math.abs($('#doscientos_pesos_close').val()));
                total_amount = parseFloat(total_amount)+parseFloat($('#doscientos_pesos_close').val())* 200;
            }else{
                $('#doscientos_pesos_close').val(0);
            }

            if($('#quinientos_pesos_close').val()!= 0 && $('#quinientos_pesos_close').val()!= '' ){
                $('#quinientos_pesos_close').val(Math.abs($('#quinientos_pesos_close').val()));
                total_amount = parseFloat(total_amount)+parseFloat($('#quinientos_pesos_close').val())* 500;
            }else{
                $('#quinientos_pesos_close').val(0);
            }

            if($('#mil_pesos_close').val()!= 0 && $('#mil_pesos_close').val()!= '' ){
                $('#mil_pesos_close').val(Math.abs($('#mil_pesos_close').val()));
                total_amount = parseFloat(total_amount)+parseFloat($('#mil_pesos_close').val())* 1000;
            }else{
                $('#mil_pesos_close').val(0);
            }

            $('#amount_close').val(total_amount);

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
            var self= this;
            self._super(options);

            $('#un_peso_close').focus(function(){
                this.select();
            });

            $('#un_peso_close').focus();
			$('#un_peso_close').val(0);
			$("#amount_close").attr('readonly','readonly');

			$('#un_peso_close').on('change',function(){
			    self.calculate_retirement_amount_close();
			});

			$('#dos_pesos_close').on('change',function(){
			    self.calculate_retirement_amount_close();
			});

			$('#cinco_pesos_close').on('change',function(){
			    self.calculate_retirement_amount_close();
			});

			$('#diez_pesos_close').on('change',function(){
			    self.calculate_retirement_amount_close();
			});

			$('#veinte_pesos_close').on('change',function(){
			    self.calculate_retirement_amount_close();
			});

			$('#cincuenta_pesos_close').on('change',function(){
			    self.calculate_retirement_amount_close();
			});

			$('#cien_pesos_close').on('change',function(){
			    self.calculate_retirement_amount_close();
			});

			$('#doscientos_pesos_close').on('change',function(){
			    self.calculate_retirement_amount_close();
			});

			$('#quinientos_pesos_close').on('change',function(){
			    self.calculate_retirement_amount_close();
			});

	        $('#mil_pesos_close').on('change',function(){
			    self.calculate_retirement_amount_close();
			});

            $('.button.acceptwidthdrawClose').on('click',function(){
				$('.button.acceptwidthdrawClose').hide()
                var amount_out = parseFloat($('#amount_close').val());

				if (amount_out <= 0  || isNaN(amount_out)){
					$("#amount_close").css("background-color","burlywood");
					setTimeout(function(){
						$("#amount_close").css("background-color","");
					},100);
					setTimeout(function(){
						$("#amount_close").css("background-color","burlywood");
					},200);
					setTimeout(function(){
						$("#amount_close").css("background-color","");
					},300);
					setTimeout(function(){
						$("#amount_close").css("background-color","burlywood");
					},400);
					setTimeout(function(){
						$("#amount_close").css("background-color","");
					},500);
					$('.button.acceptwidthdrawClose').show()
					return;
				}else{
				    var denominations = {};
                    var text_denominations = [];

			        $('#denominacion_billetes_close tr td input').each(function(){
			            if ($(this).attr('name') != 'amount_close'){
                            denominations[$(this).attr('name')] = parseFloat($(this).val());
			            }
			        });

			        $('#denominacion_billetes_close tr td input').each(function(){
			            if ($(this).attr('name') != 'amount_close'){
                            var denominations2 = {
                                'denomination': '$ '+ self.number_format($(this).attr('name'),2),
                                'qty': self.number_format(parseFloat($(this).val()),2),
                                'amount': '$ '+ self.number_format($(this).attr('name')* $(this).val(),2),
                                }
                            text_denominations.push(denominations2);
                        }
			        });

					var amount = parseFloat($('#amount_close').val());
					var reason =  'retiro';

					/*new Model('pos.session').call(
					    'set_cash_box_out_value',
					    [self.pos.pos_session.id,
					        {
                                'amount': amount_out,
                                'reason': reason,
                                'ref' : self.pos.pos_session.name,
                                'comment': '',
                                'denominations': denominations,
                            }
                        ])*/
                    rpc.query({
                        model:'pos.session',
                        method: 'set_cash_box_out_value',
                        args: [self.pos.pos_session.id,
					        {
                                'amount': amount_out,
                                'reason': reason,
                                'ref' : self.pos.pos_session.name,
                                'comment': '',
                                'denominations': denominations,
								'sucursal_id': self.pos.config.sucursal_id[0],
								'check_cash': false
                            }
                        ]
                        },{
                            timeout:5000,
                            shadow:true
                        }).then(function(last_id_out){
                            var date    = new Date();
                            var company = self.pos.company;
                            var receipt = {
							    NameSession: self.pos.pos_session.name,
							    cashier: self.pos.get_cashier().name || self.pos.user.name,
							    moneyOut: self.number_format(parseFloat(amount_out),2),
							    reason: 'retiro',
							    comment: '',
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
							self.gui.close_popup();

						    ///
						    setTimeout(function(){window.print()},1000)

							setTimeout(function(){window.print()},1500)
								///


							/*new Model('pos.session').call('get_cash_register_total_entry_encoding',
							    [
							        self.pos.pos_session.id
							    ])*/
							rpc.query({
							    model:'pos.session',
							    method: 'get_cash_register_total_entry_encoding',
							    args:[
							        self.pos.pos_session.id
							    ]
							    },{
							        timeout:5000,
							        shadow:true,
							    }).then(function(cash_register_total_entry_encoding){
							        self.pos.pos_session.cash_register_total_entry_encoding = cash_register_total_entry_encoding;
							    }).catch(function(){
							        self.gui.show_popup('error',{
							            title: 'Error de consulta.',
							            body: 'No se pudo obtener la diferencia en efectivo para el cierre.'
							        });
							    })

							setTimeout(function(){
							    self.gui.show_popup('ConfirmationClosePopupWidget',{
							        session: self.pos.pos_session,
							    });
							},1500);

							setTimeout(function(){
							    $('.button.acceptConfirmationClose').click()
							},6000);


					}).catch(function(unused, event){
					    self.gui.close_popup();
					    self.gui.show_popup('error', {
							title: 'No se registró el retiro en el sistema.',
							body: 'Por favor revisa la conexión a internet.',
						});
						event.preventDefault();
					});
					//self.gui.close_popup();
				}
            });
        },
    });

    gui.define_popup({name:'CloseCashPopupWidget',widget: CloseCashPopupWidget});

    reprint_ticket.PopUpMenu.include({

		show: function(options){
			var self = this;
			self._super(options);

			$('.gridView-toolbar.closeSessionButton').on('click',function(){

			     /// REvisa que todas las facturas generadas esten timbradas para proceder con el cierre
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
                                body:'Hay facturas que no fueron timbradas exitosamente.\n Para realizar el cierre es necesario timbrarlas:  '+ orders +'\n.'
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

				var close_pass = self.gui.ask_password_smay('cierre de caja');
				var difference_fund = self.pos.pos_session.cash_register_balance_start - self.pos.pos_session.cash_register_balance_end_real;

                close_pass.done(function(){

                /*new Model('pos.config').call('existe_conexion',[],undefined,{timeout:2000})*/
                rpc.query({
                    model:'pos.config',
                    method: 'existe_conexion',
                    args:[],

                },{
                timeout:5000,
                shadow:true

                }).then(function(resp){
                    if(difference_fund > 0){
                        self.gui.show_popup('withdrawFundCashPopupWidget',{
                            'difference_fund': difference_fund
                        });
                    }else{
                        self.gui.show_popup('CloseCashPopupWidget')
                    }
                    }).catch(function(){
                    self.gui.show_popup('error',
                        {
                            title: 'Sin conexión al servidor.',
                            body:'No hay comunicación con el servidor, intentalo más tarde. Notifica al personal de sistemas.'
                        });
                    })
                });
			});

			$('.button.close').on('click',function(){
				self.gui.close_popup();
			});
		}
	});
});
