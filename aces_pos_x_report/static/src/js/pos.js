odoo.define('aces_pos_x_report.aces_pos_x_report', function (require) {
"use strict";

var gui = require('point_of_sale.gui');
var models = require('point_of_sale.models');
var screens = require('point_of_sale.screens');
var core = require('web.core');
//var Model = require('web.DataModel');
var rpc = require('web.rpc');
var ActionManager = require('web.ActionManager');
var reprint_ticket = require('smay_reprint_ticket.smay_reprint_ticket');

var QWeb = core.qweb;

    /*var XReportButton = screens.ActionButtonWidget.extend({
        template: 'XReportButton',
        button_click: function(){
        	var self = this;
        	var pos_session_id = self.pos.pos_session.id;
        	new Model("report").call('get_html', [pos_session_id, 'aces_pos_x_report.front_sales_thermal_report_template']).done(
				function(report_html) {
					if(self.pos.config.iface_print_via_proxy && self.pos.proxy.get('status').status === "connected"){
                        self.pos.proxy.print_receipt(report_html);
                    } else {
                    	var print = {'context': {'active_id': [pos_session_id],
                            'active_ids':[pos_session_id]},
                            'report_file': 'aces_pos_x_report.front_sales_report_pdf_template',
                            'report_name': 'aces_pos_x_report.front_sales_report_pdf_template',
                            'report_type': "qweb-pdf",
                            'type': "ir.actions.report.xml"};
			                var options = {};
			                var action_manager = new ActionManager();
			                action_manager.ir_actions_report_xml(print);
                    }
				}
			);
        },
    });

    screens.define_action_button({
        'name': 'xreport',
        'widget': XReportButton,
        'condition': function(){
            return this.pos.config.print_x_report;
        },
    });*/

    reprint_ticket.PopUpMenu.include({
        show: function(options){
            var self = this;
			self._super(options);
			$('.gridView-toolbar.closeReportButton').on('click',function(){

                ///if(self.pos.user.role =='manager'){
                    var close_report = self.gui.ask_password_smay('Reporte de Arqueo/Cierre');
                    close_report.done(function(){
                        var pos_session_id = self.pos.pos_session.id;
                        rpc.query(
                            {
                            model:'pos.config',
                            method:'existe_conexion',
                            args:[],
                            timeout: 5000,
                            shadow: true,
                            }
                        ).then(function(data){

                            if(self.pos.config.enable_x_report) {
                                var pos_session_id = [self.pos.pos_session.id]
                                self.pos.chrome.do_action('aces_pos_x_report.report_pos_sales_pdf_front',{additional_context:{
                                    active_ids: pos_session_id,
                                }}).catch(function(){
                                    self.pos.gui.show_popup('error','Error al generar el reporte');
                                });
                            }else{
                                self.pos.gui.show_popup('error', 'No esta habilitado en la configuración del punto de venta para imprimir el reporte');
                            }


                        }).catch(function(){
                            self.pos.gui.show_popup('error','No Hay conexión con el servidor.')
                            }
                            );
                    });
                /*}else
                    self.pos.gui.show_popup('error','No tienes los privilegios para generar el reporte.')*/
            });
		}
	});
});
