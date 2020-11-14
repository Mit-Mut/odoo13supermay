# -*- coding: utf-8 -*-
{
    'name': "smay_reprint_ticket",

    'summary': """
        Reprint pos order ticket.""",

    'description': """
        This module allows to reprint a pos order ticket.
    """,

    'author': "Gerardo Reyes Preciado",
    'website': "http://www.smay.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Point of Sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'smay_custom_ticket', 'smay_custom_pos', 'pos_user_restrict'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ]
}
