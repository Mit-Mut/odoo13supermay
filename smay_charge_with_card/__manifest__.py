# -*- coding: utf-8 -*-
{
    'name': "SMAY Extra Charge",

    'summary': """
        Adds an extra charge when paid with card.""",

    'description': """
        This module adds an extra charge when paid with card.
    """,

    'author': "Gerardo Reyes Preciado",
    'website': "http://www.supermay.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Point Of sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'smay_custom_ticket', ],

    # always loaded
    'data': [
        'views/views.xml',
        'views/templates.xml',
    ],

    'qweb': [
        'static/src/xml/pos.xml',
    ]
}
