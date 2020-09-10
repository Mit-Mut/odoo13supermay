odoo.define('smay_pos_invoice.smay_pos_invoice', function (require) {
"use strict";

    var models = require('point_of_sale.models');
    var popups = require('point_of_sale.popups');
    var gui = require('point_of_sale.gui');
    var screens = require('point_of_sale.screens');
    var rpc = require('web.rpc');

    models.load_models([
        {
            //model: 'pos.order',
            //fields: ['id','pos_reference'],

            model: 'l10n_mx_edi.payment.method',
            fields: ['id','name'],
            label: 'Facturación SAT',

            loaded: function(self,facturacion_sat_metodos_pago){
                self.facturacion_usos_cfdi = {};
                var facturacion_sat_metodos_pago=[]

                facturacion_sat_metodos_pago.push( {'id':1, 'name': 'Efectivo'})
                facturacion_sat_metodos_pago.push( {'id':2, 'name': 'Cheque nominativo'})
                facturacion_sat_metodos_pago.push({'id':3, 'name': 'Transferencia electrónica de fondos'})
                facturacion_sat_metodos_pago.push({'id':4, 'name': 'Tarjeta de Crédito'})
                facturacion_sat_metodos_pago.push({'id':5, 'name': 'Monedero Electrónico'})
                facturacion_sat_metodos_pago.push({'id':6, 'name': 'Dinero Electrónico'})
                facturacion_sat_metodos_pago.push({'id':7, 'name': 'Vales de despensa'})
                facturacion_sat_metodos_pago.push({'id':8, 'name': 'Dación de pagos'})
                facturacion_sat_metodos_pago.push({'id':9, 'name': 'Pago por subrogración'})
                facturacion_sat_metodos_pago.push({'id':10, 'name': 'Pago por consignación'})
                facturacion_sat_metodos_pago.push({'id':11, 'name': 'Condonación'})
                facturacion_sat_metodos_pago.push({'id':12, 'name': 'Compensación'})
                facturacion_sat_metodos_pago.push({'id':13, 'name': 'Novacion'})
                facturacion_sat_metodos_pago.push({'id':14, 'name': 'Confusión'})
                facturacion_sat_metodos_pago.push({'id':15, 'name': 'Remisión de deuda'})
                facturacion_sat_metodos_pago.push({'id':16, 'name': 'Prescripción o caducidad'})
                facturacion_sat_metodos_pago.push({'id':17, 'name': 'A satisfacción del cliente'})
                facturacion_sat_metodos_pago.push({'id':18, 'name': 'Tarjeta de Débito'})
                facturacion_sat_metodos_pago.push({'id':19, 'name': 'Tarjeta de Servicio'})
                facturacion_sat_metodos_pago.push({'id':20, 'name': 'Aplicación de anticipos'})
                facturacion_sat_metodos_pago.push({'id':21, 'name': 'Intermediario pagos'})
                facturacion_sat_metodos_pago.push({'id':22, 'name': 'Por definir'})

                self.facturacion_usos_cfdi['G01']= "Adquisición de mercancías."
                self.facturacion_usos_cfdi['G02']= "Devoluciones, descuentos o bonificaciones."
                self.facturacion_usos_cfdi['G03']= "Gastos en general."
                self.facturacion_usos_cfdi['I01']= "Construcciones."
                self.facturacion_usos_cfdi['I02']= "Mobilario y equipo de oficina por inversiones."
                self.facturacion_usos_cfdi['I03']= "Equipo de transporte."
                self.facturacion_usos_cfdi['I04']= "Equipo de cómputo y accesorios."
                self.facturacion_usos_cfdi['I05']= "Dados, troqueles, moldes, matrices y herramental."
                self.facturacion_usos_cfdi['I06']= "Comunicaciones telefónicas."
                self.facturacion_usos_cfdi['I07']= "Comunicaciones satelitales."
                self.facturacion_usos_cfdi['I08']= "Otra maquinaria y equipo."
                self.facturacion_usos_cfdi['D01']= "Honorarios médicos, dentales y gastos hospitalarios."
                self.facturacion_usos_cfdi['D02']= "Gastos médicos por incapacidad o discapacidad."
                self.facturacion_usos_cfdi['D03']= "Gastos funerales."
                self.facturacion_usos_cfdi['D04']= "Donativos."
                self.facturacion_usos_cfdi['D05']= "Intereses reales efectivamente pagados por créditos hipotecarios (casa habitación)."
                self.facturacion_usos_cfdi['D06']= "Aportaciones voluntarias al SAR."
                self.facturacion_usos_cfdi['D07']= "Primas por seguros de gastos médicos."
                self.facturacion_usos_cfdi['D08']= "Gastos de transportación escolar obligatoria."
                self.facturacion_usos_cfdi['D09']= "Depósitos en cuentas para el ahorro, primas que tengan como base planes de pensiones."
                self.facturacion_usos_cfdi['D10']= "Pagos por servicios educativos (colegiaturas)."
                self.facturacion_usos_cfdi['P01']= "Por definir."

                self.facturacion_sat_metodos_pago= facturacion_sat_metodos_pago;
            },
        },
    ],{
    'after': 'pos.config'
    });

    var _super_ReceiptScreenWidget = screens.ReceiptScreenWidget;
    _super_ReceiptScreenWidget = screens.ReceiptScreenWidget.include({
        show: function(){
            this._super();
            var self = this;
            if(self.pos.get_order().to_invoice){
                setTimeout(function(){
                    rpc.query({
                        model: 'pos.order',
                        method: 'check_successful_invoice',
                        args: [this.posmodel.get_order().name],
                        timeout: 2000,
                    }).then(function(order) {
                        if(order==false){
                            self.gui.show_popup('error',{
                                title: 'Error en la Factura',
                                body: "La factura generada por la orden: "+self.pos.get_order().name+" no fue timbrada. \n\n Revisa el RFC del cliente.",
                            })
                            $('.popup-error').width(650)
                            $('.popup-error').height(200)
                        }
                    })
                }, 3000)
            }
        },
    });


    var _super_order = models.Order;
    models.Order = models.Order.extend({

        initialize: function(attributes,options){
            _super_order.prototype.initialize.apply(this, arguments);
            this.x_metodo_pago_sat = '';
            this.x_uso_cfdi_sat = '';
            return this;
        },

        export_as_JSON: function() {
            var json = _super_order.prototype.export_as_JSON.apply(this,arguments);
            json.x_metodo_pago_sat =  this.x_metodo_pago_sat;
            json.x_uso_cfdi_sat = this.x_uso_cfdi_sat;
            return json;
        },

        set_uso_cfdi: function(id){
            this.x_uso_cfdi_sat = id;
        },

        set_pay_method: function(id){
            this.x_metodo_pago_sat = id;
        },

        get_uso_cfdi: function(id){
            return self.pos.facturacion_usos_cfdi[id]
        },

        get_metodo_pago_sat:function(id){
            var metodo=''
            self.pos.facturacion_sat_metodos_pago.forEach(function(element){
                if(parseInt(element['id'])=== parseInt(id)){
                    metodo= element['name']}
                })
            if(metodo!='') return metodo
        },

    });


    var invoicePopupWidget = popups.extend({
        template: 'invoicePopupWidget',

        show: function(options){
            this._super(options);
            var order = self.pos.get_order();
            $('#accept14').on('click', function() {
                order.set_pay_method($('#metodo_pago').children('option:selected').val());
                order.set_uso_cfdi($('#uso_cfdi').children('option:selected').val());
                self.pos.gui.close_popup();
                if(!order.get_client()){
                    self.pos.gui.show_screen('clientlist');
                }else{
                    self.pos.gui.show_popup('ConfirmInvoicePopupWidget',{
                        'title': 'Información a Facturar',
                    })
                }
            });

            $('#cancel14').on('click', function() {
                order.set_uso_cfdi(null);
                order.set_pay_method(null);
				self.pos.get_order().remove_all_paymentlines()
                self.pos.get_order().set_client(null)
                self.pos.get_order().set_to_invoice(false)
                self.pos.gui.close_popup();
                self.$('.js_invoice').removeClass('highlight');
                order.set_to_invoice(false);
				self.pos.gui.screen_instances.payment.renderElement()
             });
        },
    });

    gui.define_popup({
        name: 'invoicePopupWidget',
        widget: invoicePopupWidget,
    });

    var ConfirmInvoicePopupWidget = popups.extend({
        template: 'ConfirmInvoicePopupWidget',

        show: function(options){
            this._super(options);
            var order = self.pos.get_order();
            $('#aceptar_data_invoice').on('click', function() {
                self.pos.gui.close_popup();
				if(self.pos.get_order().get_client() && !self.pos.get_order().get_client().vat){
					order.set_uso_cfdi(null);
					order.set_pay_method(null);
					self.pos.get_order().remove_all_paymentlines()
					self.pos.get_order().set_client(null)
					self.pos.get_order().set_to_invoice(false)
					self.pos.gui.close_popup();
					self.$('.js_invoice').removeClass('highlight');
					order.set_to_invoice(false);
					self.pos.gui.screen_instances.payment.renderElement()
					self.pos.gui.show_popup('error',{
						'title': 'Error en cliente',
						'body': 'El cliente no tiene asignado RFC.'
					})
					$('.popup.popup-error').css('height','200px')

                }
            });

            $('#cancelar_data_invoice').on('click', function() {
                order.set_uso_cfdi(null);
                order.set_pay_method(null);
				self.pos.get_order().remove_all_paymentlines()
                self.pos.get_order().set_client(null)
                self.pos.get_order().set_to_invoice(false)
                self.pos.gui.close_popup();
                self.$('.js_invoice').removeClass('highlight');
                order.set_to_invoice(false);
				self.pos.gui.screen_instances.payment.renderElement()
            });
        },
    });

    gui.define_popup({
        name: 'ConfirmInvoicePopupWidget',
        widget: ConfirmInvoicePopupWidget,
    });


     var _super_PaymentScreenWidget = screens.PaymentScreenWidget;
    _super_PaymentScreenWidget = screens.PaymentScreenWidget.include({

        click_invoice: function(){
            var order = this.pos.get_order();
            order.set_to_invoice(!order.is_to_invoice());
            if (order.is_to_invoice()) {
                self.$('.js_invoice').addClass('highlight');
                this.pos.gui.show_popup('invoicePopupWidget',{
                        'title':'Opciones de Facturación',
                });
            } else {
                self.$('.js_invoice').removeClass('highlight');
            }
        },

        customer_changed: function() {
            this._super();
            if(self.pos.get_order().is_to_invoice()&&self.pos.get_order().get_client()){
                setTimeout(function(){
                    self.pos.gui.show_popup('ConfirmInvoicePopupWidget',{
                        'title': 'Información a Facturar',
                    }), 2000})
            }
        },
    });

});
