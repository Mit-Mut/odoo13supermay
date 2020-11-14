# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
    "name": "POS Cash Drawer Alert",
    "summary": "This module raises an alert once the cash drawer reaches a specified threshold limit",
    "category": "Point Of Sale",
    "version": "1.0",
    "sequence": 1,
    "author": "Webkul Software Pvt. Ltd.",
    "license": "Other proprietary",
    "website": "https://store.webkul.com/Odoo-POS-Cash-Drawer-Alert.html",
    "description": "https://webkul.com/blog/odoo-pos-cash-drawer-alert/",
    "live_test_url": "http://odoodemo.webkul.com/?module=pos_cash_alert&version=12.0&custom_url=/pos/web",
    "depends": ['base', 'smay_reprint_ticket', 'point_of_sale'],
    "data": [
        'views/pos_config.xml',
        'views/templates.xml',
        'security/ir.model.access.csv',
    ],
    # "demo"                 :  ['data/pos_cash_alert_demo.xml'],
    "qweb": ['static/src/xml/pos_cash_alert.xml', 'static/src/xml/pos.xml'],
    "images": ['static/description/Banner.png'],
    "application": True,
    "installable": True,
    "auto_install": False,
    "price": 27,
    "currency": "EUR",
    "pre_init_hook": "pre_init_check",
}
