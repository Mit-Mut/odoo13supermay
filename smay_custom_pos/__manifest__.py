# -*- coding: utf-8 -*-
{
    'name': "SMAY custom pos",

    'summary': "Modifications of POS.",

    'description': "This module modifies the Point of Sale. ",

    'author': "Gerardo Reyes Preciado",
    'website': "http://www.supermay.mx",

    'category': 'Point Of Sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale','base', 'pos_user_restrict'],

    # always loaded
    'data': [
        #'views/views.xml',
        'views/templates.xml',
    ],
}
