# -*- coding: utf-8 -*-
{
    'name': "smay_refunds",

    'summary': """
        Refunds from Point of Sale""",

    'description': """
        This module allows to refund an order from point of sale.
    """,

    'author': "Gerardo Reyes Preciado",
    'website': "http://www.smay.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Point of sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'smay_reprint_ticket', 'point_of_sale'],

    # always loaded
    'data': [

        'views/views.xml',
        'views/templates.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml', 
    ]
}
