# -*- coding: utf-8 -*-
{
    'name': "smay_stock_transferences",

    'summary': """
        Customization of transfers of stock.""",

    'description': """
        This module modifies how to do the transfers of stock.
    """,

    'author': "Gerardo Reyes Preciado",
    'website': "http://www.supermay.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock'],

    # always loaded
    'data': [
        #'security/transfers_restrict_user.xml',
        # 'views/views.xml',
    ],
}
