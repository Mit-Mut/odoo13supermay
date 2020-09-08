# -*- coding: utf-8 -*-
{
    'name': "smay_close_pos",

    'summary': """
        Close the point of sale session.""",

    'description': """
        This module allows to close the point of sale session from the interface.
    """,

    'author': "Gerardo Reyes Preciado.",
    'website': "http://www.supermay.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Point of Sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'pos_cash_alert'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        'views/templates.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ]
}
