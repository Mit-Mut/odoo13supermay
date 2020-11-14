# -*- coding: utf-8 -*-
{
    'name': "smay_reconciliation_of_withdrawals",

    'summary': """
        Conciliation of pos withdrawals""",

    'description': """
        This module allows to conciliation of pos withdrawals.
    """,

    'author': "Gerardo Reyes Preciado",
    'website': "http://www.supermay.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Point of Sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale'],# 'stock', 'web'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/report.xml',
        'views/report_template.xml',
    ],
}
