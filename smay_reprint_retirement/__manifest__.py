# -*- coding: utf-8 -*-
{
    'name': "smay_reprint_retirement",

    'summary': """
        Reprint the retirements""",

    'description': """
        This module allows to reprint the cash retirements.
    """,

    'author': "Gerardo Reyes Preciado",
    'website': "http://www.supermay.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'point_of_sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'pos_cash_alert', 'smay_reprint_ticket'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        #'views/views.xml',
        'views/templates.xml',
    ],

    'qweb': [
        'static/src/xml/pos.xml',
    ]
}
