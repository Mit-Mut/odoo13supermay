# -*- coding: utf-8 -*-
{
    'name': "pos_invoice",

    'summary': """
        The module shows the options for invoicing""",

    'description': """
        This module shows the options for the cashier selects payment_method and use_cfdi.
    """,

    'author': "Gerardo Reyes Preciado",
    'website': "http://www.supermay.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'point_of_sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale'],

    # always loaded
    'data': [
        'views/views.xml',
        'views/templates.xml',
    ],
    'qweb': ['static/src/xml/invoice.xml']
}
