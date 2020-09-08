odoo.define('smay_reprint_retirement.smay_reprint_retirement', function(require){
'use strict';

    var gui = require('point_of_sale.gui');
    var popups = require('point_of_sale.popups');
    var reprint_ticket = require('smay_reprint_ticket.smay_reprint_ticket');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var QWeb = core.qweb;

    var reprintRetirementWidget = popups.extend({
        template:'reprintRetirementWidget',

        get_correct_datetime : function(date){
            var correct_datetime = new Date(date+' UTC').toString();
            var correct_date = date.substring(0,10);
            var correct_time = correct_datetime.substring(16,24);
            return correct_date.substring(8,10)+'/'+correct_date.substring(5,7)+'/'+correct_date.substring(0,4) +' '+correct_time;
	    },

        show: function(options){
            var self= this;
            self._super(options);

            $('.button.acceptReprintRetirement').on('click', function(){
                var folio = $('.folio_retiro').val();
                var sucursal_id = self.pos.config.sucursal_id[0];
                self.gui.close_popup();

                if(folio==''){
                    self.pos.gui.show_popup('error',{
                        'title': 'Error de folio',
                        'body': 'Debe ser ingresado un folio',
                    });
                    $('.popup.popup-error').css('height','200px');
                    return
                }

                if(folio%1 >0){
                    self.pos.gui.show_popup('error',{
                        'title': 'Error de Folio',
                    'body': 'El folio debe ser un número entero',
                    })
                    $('.popup.popup-error').css('height','200px')
                    return
                }

                rpc.query({
			        model : 'pos.config',
					method: 'existe_conexion',
					args:[],
				}).then(function(resp){
				    rpc.query({
				    model:'pos.config',
				    method: 'get_data_retirement',
				    args:[folio,sucursal_id,self.pos.config.id],
                    timeout: 3000,
				    }).then(function(resp){

				        if(resp==0){
				            self.pos.gui.show_popup('error',{
				                'title': 'Retiro fuera de rango',
				                'body': 'El retiro esta fuera de los '+self.pos.config.days_of_reprint+' días permitidos para reimprimir.'
				            })
				            $('.popup.popup-error').css('height','200px');
				            return;
				        }

				        if(resp==-1){
				            self.pos.gui.show_popup('error',{
				                'title': 'Retiro no existe',
				                'body': 'El retiro no fue encontrado.'
				            })
				            $('.popup.popup-error').css('height','200px');
				            return;
				        }

				        //setTimeout(function(){
							var date    = new Date();
							var company = self.pos.company;
							var receipt = {
								NameSession: self.pos.pos_session.name,
								cashier: resp['cashier'],
								moneyOut: resp['moneyOut'],
								reason: resp['reason'],
								comment: resp['comment'],
								last_id_out: folio,
								precision: {
									price: 2,
									yeaey: 2,
									quantity: 3,
								},
								date: {
									year: date.getFullYear(),
									month: date.getMonth(),
									date: date.getDate(),
									day: date.getDay(),
									hour: date.getHours(),
									minute: date.getMinutes() ,
									isostring: date.toISOString(),
									localestring: self.get_correct_datetime(resp['date_retirement']),
								},
								company:{
									name: company.name,
									phone: company.phone,
									email: company.email,
									country: company.country.name,
									website: company.website,
									logo: self.pos.company_logo_base64,
								},

								denominations: resp['denominations'],
								url_id: self.pos.attributes.origin+"/report/barcode/Code128/"+folio,
							};

							var env = {
								widget:  self,
								receipt: receipt
							};

							if(self.gui.get_current_screen() != 'receipt')
								self.gui.show_screen('receipt',{'retirement': true});

							var receiptFinal = QWeb.render('XmlReciboDeRetiro',env);
							$('.pos-receipt').html(receiptFinal);
						//}, 1000)

						//setTimeout(function(){
							var date = new Date()
							$('.leyenda_retiro').replaceWith("<img alt='Super may - Reimpresión' class='leyenda_retiro1' src='/smay_reprint_retirement/static/img/leyenda_reimpresion_retiro.JPG' style='width:100%; height:35px;'>")
							$('.leyenda_retiro1').after("<div class='pos-center-align' id='reprint_date'>Fecha de Reimpresión:"+date.getDate()+"/"+(parseInt(date.getMonth(),10)+1)+"/"+date.getFullYear()+"  "+date.getHours()+":"+date.getMinutes()+":"+date.getSeconds()+"</div>")
							$('.denominaciones').after("<br/><img alt='Super may - Reimpresión' class='leyenda_retiro' src='/smay_reprint_retirement/static/img/leyenda_reimpresion_retiro.JPG' style='width:100%; height:35px;'>")
						///}, 1300)

				    }).catch(function(){
				        self.pos.gui.show_popup('error',{
				            'title': 'Sin respuesta',
				            'body': 'No se recibio respuesta del servidor. Intenta de nuevo.'
				        });
				        $('.popup.popup-error').css('height','200px')
				    })

				}).catch(function(){
					self.pos.gui.show_popup('error',{
                        'title': 'Error de conexión',
                        'body': 'No hay conexión con el servidor, intentalo más tarde.'
                    })
                    $('.popup.popup-error').css('height','200px')
				});
            });
        },
    });

    gui.define_popup({name:'reprintRetirementWidget',widget: reprintRetirementWidget});

    reprint_ticket.PopUpMenu.include({

		show: function(options){
			var self = this;
			self._super(options);

			$('.gridView-toolbar.reprintRetirementButton').on('click',function(){
			self.pos.gui.close_popup();
			    var reprint_pass = self.gui.ask_password_smay('Reimpresion de Retiro');

			    reprint_pass.done(function(){
			        self.pos.gui.show_popup('reprintRetirementWidget',{
			        'title': 'Reimpresión de Retiro'
			        })
			    });
			})
		},
	});
});
