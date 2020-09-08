# -*- coding: utf-8 -*-
{
    'name': "smay_purchases_users",

    'summary': """
        Asigns the warehouse automatically to users.""",

    'description': """
        This module allows to asign warehouse to users for the purchases.
    """,

    'author': "Gerardo Reyes Preciado",
    'website': "http://www.supermay.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'purchase',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase', 'purchase_stock', 'stock', 'product', 'smay_price_labels'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/purchase_restrict_user.xml',
        'views/views.xml',
        # 'views/templates.xml',
    ],
}
