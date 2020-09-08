# -*- coding: utf-8 -*-
{
    'name': "smay_custom_ticket",

    'summary': """
        Custon the POS ticket""",

    'description': """
       The module modifies the pos ticket.
    """,

    'author': "Gerardo Reyes Preciado",
    'website': "http://www.supermay.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Point of Sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'pos_user_restrict', 'smay_custom_pos'],

    # always loaded
    'data': [
        'views/views.xml',
        'views/templates.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ]
}
