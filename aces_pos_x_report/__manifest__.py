# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
{
    'name': 'Pos X Report',
    'category': 'Point of Sale',
    'summary': 'This module allows user to print x-report(Mid-day sale report) from front-end.',
    'description': """
This module allows user to print x-report(Mid-day sale report) from front-end.
""",
    'author': 'Acespritech Solutions Pvt. Ltd.',
    'website': 'http://www.acespritech.com',
    'price': 35,
    'currency': 'EUR',
    'version': '1.0.1',
    'depends': ['base', 'point_of_sale', 'pos_cash_alert'],
    'images': ['static/description/main_screenshot.png'],
    "data": [
        # 'views/point_of_sale.xml',
        'views/template.xml',
        'views/front_sales_thermal_report_template.xml',
        'views/front_sales_report_pdf_template.xml',
        'views/page_reports.xml',
    ],
    'qweb': ['static/src/xml/pos.xml'],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
