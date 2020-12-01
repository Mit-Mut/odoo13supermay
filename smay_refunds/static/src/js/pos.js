odoo.define('smay_refunds.smay_refunds', function(require){
"use strict";

    var models = require('point_of_sale.models');
    var rpc = require('web.rpc')
    var reprint_ticket = require('smay_reprint_ticket.smay_reprint_ticket');
    var gui = require('point_of_sale.gui');
    var popups = require('point_of_sale.popups');
    var core = require('web.core');
    var QWeb = core.qweb;
    var screens = require('point_of_sale.screens');

    models.load_fields('res.users', 'is_manager');
    models.load_fields('pos.config', ['x_dias_permitidos_devolucion']);

    var _superOrderline = models.Orderline;
    models.Orderline = models.Orderline.extend({

    set_quantity: function(quantity, keep_price){
           if(self.pos.get_order())
                self.pos.get_order().remove_all_paymentlines();
           console.log('ORDERLINEEEEEEEEE')
           console.log(quantity)
           console.log(this)
           if(this.is_selected() && quantity % 1>0 && this.product.uom_id[1]!='kg' ){

           self.gui.show_popup('error', {
                            title: 'Cantidad Incorrecta.',
                            body: 'Solo puede ingresar cantidades enteras.',
                        });
                        $('.popup.popup-error').css({'height':'200px','width':'400px'})
						return
           }
            _superOrderline.prototype.set_quantity.apply(this,arguments);
        },

    });


    reprint_ticket.PopUpMenu.include({
        show: function(options){

            var self = this;
			self._super(options);

			$('.gridView-toolbar.refundButton').on('click',function(){
                var refund_pass = self.gui.ask_password_smay('devolucion de orden');
                refund_pass.done(function(){
                    for(var i= self.pos.get_order().get_orderlines().length-1; i>=0; i--){
                        self.pos.get_order().remove_orderline(self.pos.get_order().get_orderlines(i))
                    }
                    self.gui.show_popup('RefundPopUp');
                });
			});
        }
    });


    /*gui.Gui = gui.Gui.extend({

        ask_password_smay: function(action) {
            var self = this;
            var _managers =[];
            for(var i=0; i<self.pos.users.length; i++){
                if(self.pos.users[i].is_manager){
                    _managers.push(self.pos.users[i].pos_security_pin);
                }
            }

            var ret = new $.Deferred();
                this.show_popup('password',{
                    'title': 'Contraseña',
                    confirm: function(pw) {
                        if(!_managers.includes(pw)){
                            self.show_popup('error','Contraseña incorrecta');
                            ret.reject();
                        } else {
                            ret.resolve();
                        }
                    },
                });
            return ret;
        },
    });*/

    var RefundPopUp = popups.extend({
        template : 'RefundPopUp',
        show: function(options){
            var self = this;
			self._super(options);
			self.pos.refund_order = false;
			$('#refund_order').focus();
            $('#refund_accept').on('click',function(){

			self.gui.close_popup();
			if($('#refund_order').val() == ""){
			    self.gui.show_popup('error',{
                    title: 'Error en la orden',
                    body: 'El campo no puede estar vacio'
		        });
			    return;
			}

			rpc.query({
			    model : 'pos.config',
				method : 'existe_conexion',
				args: [],
				timeout: 2000,
				}).then(function(resp){
                    rpc.query({
                        model: 'pos.order',
                        method: 'exist_order',
                        //args:[$('#refund_order').val()],
                        //args:['Pedido '+ $('#refund_order').val().replace(/ /g,'-')],
                        args:[ $('#refund_order').val().replace(/ /g,'-')],
                        timeout: 5000,
                        }).then(function(resp){
                            if(resp == -1 ){
                                self.gui.show_popup('error', {
                                    title:'Orden invalida',
                                    body: 'No se puede hacer devolución de una orden que ya le fue aplicada.'
                                });
                                return;
                            }

                            if(resp == -2){
                                self.gui.show_popup('error', {
                                    title:'Orden invalida',
                                    body: 'No se encontro la orden. Revisa la información ingresada y/o que el usuario este bien configurado.'
                                });
                                return;
                            }
                            if(resp == -3){
                                self.gui.show_popup('error', {
                                    title:'Orden invalida',
                                    body: 'La orden excede los '+ self.pos.config.x_dias_permitidos_devolucion+' permitidos para la devolución.'
                                });
                                return;
                            }

                            if(resp > 0){
                                self.pos.config.iface_print_auto  = false;
                                    rpc.query({
                                        model:'pos.order',
                                        method : 'get_information_reprint',
                                        args: [resp, true],
                                        timeout:5000,
                                    }).then(function(data){
                                        self.pos.gui.show_popup('RefundOrderInformationPopUp',{
                                            title: data.pos_reference+ '       Total :  ' +self.format_currency(data.total,2)  ,
                                            order:data,
                                        });
                                    });
                            }
                        }).catch(function(){
                            self.pos.gui.show_popup('error',{
                                title: 'Devolución',
                                body: 'No existe la orden.'
                            });
                        });
                }).catch(function(){
				    self.pos.gui.show_popup('error',{
                        title: 'Devolución',
                        body: 'No hay conexion con el servidor, intentalo más tarde.',
                    });
                });
            });

            $('#refund_cancel').on('click',function(){
				self.gui.close_popup();
				self.pos.refund_order = false;
			});
        }
    });

    gui.define_popup({name:'RefundPopUp',widget: RefundPopUp});

    var RefundOrderInformationPopUp = popups.extend({
        template: 'RefundOrderInformationPopUp',

        get_correct_datetime : function(date){
            var correct_datetime = new Date(date+' UTC').toString();
            var correct_date = date.substring(0,10);
            var correct_time = correct_datetime.substring(16,24);
            return correct_date.substring(8,10)+'/'+correct_date.substring(5,7)+'/'+correct_date.substring(0,4) +' '+correct_time;
	    },

        show : function(options){
            var self = this;
            var error = false
            self._super(options);
            if(options){
                var orderlines = options.order.orderlines;
                $("#original_order").append("
                        <table style='width: 100%;'>
                            <tr>
                                <th style='width: 45%;' align='center'>
                                    Producto
                                </th>
                                <th style='width: 15%;' align='center';>
                                    Cant. Devolver
                                </th>
                                <th style='width: 10%;' align='center';>
                                    Cant.
                                </th>
                                <th style='width: 20%;' align='center';>
                                    Precio Unit.
                                </th>
                                <th style='width: 20%;' align='center';>
                                    Subtotal
                                </th>
                            </tr>
                        </table>"
                        );

                for(var i = 0; i < orderlines.length; i++){

                    $("#original_order").append("
                            <table style='width: 100%;'>
                                <tr class='orderline'>
                                    <td style='width: 45%;padding=10px 5px' align='left'>
                                        <div style='text-align:left; padding:0px 15px' class='product_name'>"+
                                            orderlines[i].name_product
                                        +"</div>
                                    </td>
                                    <td style='width: 15%' align='center'>
                                    <input type='number' value='"+/*orderlines[i].qty*/ 0+"' class='orderline_qty' qty='"+orderlines[i].qty+"' style='margin:3px 0px'' >
                                    </td>
                                    <td style='width: 10%;' align='right'>"+
                                        orderlines[i].qty
                                    +"</td >

                                    <td style='width: 20%;padding=100px 100px' align='right'>
                                        <div style='text-align:right; padding : 0px 15px' class='price_unit'> "+
                                            self.format_currency(orderlines[i].price_unit,2)
                                        +"</div>
                                    </td>
                                    <td style='width: 10%;' align='right'>"+
                                        self.format_currency(orderlines[i].qty*orderlines[i].price_unit,2)
                                    +"</td >
                                </tr>
                            </table>"
                            );
                }

                $('.orderline_qty').on('change', function(){
                    $('.orderline_qty').each(function(){
                        if( $(this).val()==''){
                            alert('No puede ir vacio el campo o debe ser cantidad real')
                            $(this).val('0')
                            error= true
                            return
                        }

                        if(parseInt($(this).val(),10)<0 || parseInt($(this).val(),10) > parseInt($(this).attr('qty'),10)){
                            alert('El valor ingresado debe ser mayor a 0 y menor que la cantidad vendida.')
                            $(this).val('0')
                            error=true
                            return
                        }

                        if(parseFloat($(this).val(),10)%1 > 0){
                            alert('El valor ingresado debe ser entero')
                            $(this).val('0')
                            error=true
                            return
                        }
                    })
                })
            }

            $("#RefundOrderTotal").on('click',function(){
                $('.orderline_qty').each(function(){
                    $(this).val($(this).attr('qty'))
                })
            });

            $('#motivo_select').on('change', function(){
                if($('#motivo_select').val().toUpperCase()!='OTRO'){
                    $('#descripcion_refund').val('')
                    $('#descripcion_refund').attr('disabled','disabled')
                    $('#descripcion_refund').val('')
                }else{
                    $('#descripcion_refund').val('')
                    $('#descripcion_refund').prop('disabled',false)

                }
            })

            //$('#descripcion_refund').val('')

            $("#OriginalOrderAccept").on('click', function(){
            /*$("#OriginalOrderAccept").hide()
            $('#OriginalOrderCancel').hide();
            $('#RefundOrderTotal').hide();*/
            /*for(var i=0; i<self.pos.get_order().get_orderlines().length; i++){
                    self.pos.get_order().remove_orderline(self.pos.get_order().get_orderlines()[i])

            }*/

                var order=[]
                var qty_of_products=0


                $('.orderline').each(function(){
                    var orderline={}
                    qty_of_products+=$(this).find('.orderline_qty').val()
                    orderline['product']=$(this).find('.product_name').html()
                    orderline['cantidad']= $(this).find('.orderline_qty').val()
                    orderline['precio_unitario'] =self.format_currency_no_symbol($(this).find('.price_unit').html(),2)
                    orderline['motivo'] = $('#motivo_select').val().toUpperCase()
                    if($('#descripcion_refund').val().length > 1)  orderline['descripcion_devolucion'] = $('#descripcion_refund').val()

                    order.push(orderline)
                })

                if( $('#motivo_select').val().toUpperCase() =='OTRO' && $('#descripcion_refund').val().length <=1){
                    alert('Es necesario ingresar la descripción para este motivo. ')
                    $("#OriginalOrderAccept").show()
                    error = false
                    return
                }
                //return
                if(qty_of_products<=0){
                    alert('Ingresa cantidades a devolver, el número de productos es 0.')
                    $("#OriginalOrderAccept").show()
                    error = false
                    return
                }

                if(error){
                $("#OriginalOrderAccept").show()
                error = false
                return}

                $("#OriginalOrderAccept").hide()
                $('#OriginalOrderCancel').hide();
                $('#RefundOrderTotal').hide();
                $("#motivo_select").hide()
                $("#descripcion_refund").hide()

                console.log('session id: '+self.pos.get_order().session_id)
                console.log('option '  +options.order.session_id)
                console.log(self.pos.pos_session.id)



                rpc.query({
                    model:'pos.order',
                    method: 'get_data_order',
                    args: [options.order.pos_reference,order,self.pos.pos_session.id],
                    timeout : 12000,
                }).then(function(data){
                    if(data==-2){
                        self.gui.show_popup('error', {
                            title: 'No se generó la Devolución.',
                            body: 'El total de la devolución excede el efectivo en caja.',
                        });
                        $('.popup.popup-error').css({'height':'200px','width':'400px'})
						return
                    }

                    if(data > 0){
                        self.pos.refund_order = true;
                        self.pos.gui.show_screen('receipt',{refund:'true'})


					    console.log('ID DE PEDIDO')
					    console.log(data)
					    //console.log(self.pos.get_order())

					    rpc.query({
					        model: 'pos.order',
						    method: 'order_has_invoice',
						    args: [data],
                            timeout: 10000,

					    }).then(function(data){
					    if(data >0){
					    self.pos.chrome.do_action('point_of_sale.pos_invoice_report',{additional_context:{
                                    active_ids: [data],
                                }}).catch(function(){
                                    self.pos.gui.show_popup('error','No se pudo imprimir la nota de credito');
                                });
					    }

					    })

					    /*self.pos.chrome.do_action('point_of_sale.pos_invoice_report',{additional_context:{
                                    active_ids: [data],
                                }}).catch(function(){
                                    self.pos.gui.show_popup('error','No se pudo imprimir la nota de credito');
                                });*/










                        rpc.query({
					   	    model: 'pos.order',
						    method: 'get_information_reprint',
						    args: [data,false],
                            timeout: 10000,
					    }).then(function(data){
                            /*var _order =self.pos.get_order();
                            var orderlines =_order.get_orderlines();

                            while (_order.get_orderlines().length > 0) {
                                _order.remove_orderline(_order.get_last_orderline());
                            }

                            var _refund_orderlines = data.orderlines*/
                            /*for(var i = 0; i < _refund_orderlines.length; i++){
                                var _product_id = self.pos.db.get_product_by_id(_refund_orderlines[i].product_id);
                                var _qty = Math.abs(_refund_orderlines[i].qty);
                                var _price_unit = _refund_orderlines[i].price_unit;
                                _order.add_product(_product_id,{
                                    quantity: _qty,
                                    price: _price_unit,
                                });
                            }*/

                            var date_reprint = new Date()
                            var day = (date_reprint.getDate() >= 10) ? date_reprint.getDate() : '0'+date_reprint.getDate()
                            var month  = ((parseInt(date_reprint.getMonth())+1)>=10) ?
                                                (parseInt(date_reprint.getMonth())+1) : '0'+(parseInt(date_reprint.getMonth())+1)
                            var hours =  (date_reprint.getHours() >= 10)? date_reprint.getHours() : '0'+date_reprint.getHours()
                            var minutes = (date_reprint.getMinutes() >= 10) ? date_reprint.getMinutes() : '0'+date_reprint.getMinutes()
                            var seconds = (date_reprint.getSeconds() >= 10) ? date_reprint.getSeconds() : '0'+date_reprint.getSeconds()
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
                                client : data.partner?data.partner:'Público en General',
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

                            console.log('DATA DE TICKETTTTTT'+data)
                            console.log('RECEIPT'+receipt)

                           // var reprinted_order = QWeb.render('RefoundPosTicket' ,{widget:self,receipt:receipt,refound: true});
                           var reprinted_order = QWeb.render('RefoundPosTicket' ,{widget:self,receipt:receipt,refound: true});
                            $('.pos-receipt').html(reprinted_order);
                                $('.pos-sale-ticket').css('padding','8px');
                                $('#img_reimp1').replaceWith("<img alt='Super may - Devolución' class='pos-logo' src='/smay_reprint_ticket/static/img/devolucion_leyenda.JPG' style='width:100%; height:25px; margin-top:10px'>")
                                $('#img_reimp2').replaceWith("<img alt='Super may - Devolución' class='pos-logo' src='/smay_reprint_ticket/static/img/devolucion_leyenda.JPG' style='width:100%; height:25px; margin-top:10px'>")
                                $('#reprint_date').remove()
                                if(data.x_motivo_devolucion!='OTRO')
                                    $('#articulos_orden').after("<tr id='motivo_devolucion'><td>Motivo de devolución:</td><td class='pos-right-align'>"+data.x_motivo_devolucion+"</td> </tr>")
                                else
                                $('#articulos_orden').after("<tr id='motivo_devolucion'><td>Motivo de devolución:</td><td class='pos-right-align'>"+data.x_motivo_devolucion+"</td> </tr> <tr><td colspan='2' class='pos-center-align'> Descripción: <br/>"+data.x_descripcion_devolucion+"</td></tr>")
                                //$('#img_reimp1')
                                self.pos.config.iface_print_auto  = true;
                                setTimeout(function(){window.print()},1000)

								setTimeout(function(){window.print()},1500)

                                console.log('ticket session_id'+self.pos.get_order().session_id)






                        }).catch(function(error){
                            console.log('ttttttttttttt'+error)

                            self.pos.gui.show_popup('error',{
                                title: 'Devolución',
                                body: 'No se obtuvo la información de la devolución.',
                            });
                        });



                        /*rpc.query({
					   	    model: 'pos.order',
						    method: 'get_information_reprint',
						    args: [data,false],
                            timeout: 5000,
					    }).done(function(data){
					    if (data>0){
					    self.chrome.do_action('point_of_sale.pos_invoice_report',{additional_context:{
                        active_ids:[data],}});
					    }

					    });*/
                    }
                }).catch(function(){
                    self.pos.gui.show_popup('error',{
                        title: 'Devolución',
                        body: 'Se vencio el tiempo de espera. Contacta al encargado.'
                    });
                });

                console.log('ultimo session id'+self.pos.get_order().session_id)
            });

            $("#OriginalOrderCancel").on('click', function(){
                    self.gui.close_popup();
                });
        }
    });

    gui.define_popup({name:'RefundOrderInformationPopUp',widget: RefundOrderInformationPopUp});


var _super_ReceiptScreenWidget = screens.ReceiptScreenWidget;
    _super_ReceiptScreenWidget = screens.ReceiptScreenWidget.include({

        click_next: function() {
            if(this.pos.refund_order){
                this.gui.show_screen('products');
                this.pos.refund_order = false;
                return;
            }
            this.pos.get_order().finalize();
        },
    });

    screens.NumpadWidget = screens.NumpadWidget.include({
	    applyAccessRights: function(){
            this._super();

            var cashier = this.pos.get('cashier') || this.pos.get_cashier();
            //var has_price_control_rights =  cashier.is_manager
            var has_price_control_rights =  cashier.role=='manager'

                this.$el.find('.mode-button[data-mode="price"]')
                .toggleClass('disabled-mode', !has_price_control_rights)
                .prop('disabled', !has_price_control_rights);

            this.$el.find('.mode-button[data-mode="discount"]')
                .toggleClass('disabled-mode', !has_price_control_rights)
                .prop('disabled', !has_price_control_rights);

            this.$el.find('.numpad-minus')
                .toggleClass('disabled-mode', true)
                .prop('disabled', true);
				

				/*$('.input-button').each(function(indice,elemento){
             if(elemento.textContent=='.' ){
                elemento.classList.add("disabled-mode");
                }



             })*/

            if(!has_price_control_rights && this.state.get('mode')=='price'){
                this.state.changeMode('quantity');
            }
	    },
    });
});
