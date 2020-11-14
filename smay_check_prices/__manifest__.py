# -*- coding: utf-8 -*-
{
    'name': "smay_check_prices",

    'summary': """
        This module shows a check of prices""",

    'description': """
        This module hides all the elements in the point of sale and It only shows prices to clients.
    """,

    'author': "Gerardo Reyes Preciado",
    'website': "http://www.supermay.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'point_of_sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'smay_window_product'],

    # always loaded
    'data': [
        'views/views.xml',
        'views/templates.xml',
    ],
}
