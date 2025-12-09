from __future__ import annotations

from frappe import _


def get_data():
    return [
        {
            "module_name": "Pricing Calculator",
            "category": "Modules",
            "label": _("Pricing Calculator"),
            "icon": "octicon octicon-calculator",
            "type": "module",
            "items": [
                {"type": "doctype", "name": "Pricing Item", "label": _("Pricing Item")},
                {"type": "doctype", "name": "Pricing Formula", "label": _("Pricing Formula")},
                {"type": "doctype", "name": "Calculated Quote", "label": _("Calculated Quote")},
                {"type": "page", "name": "price_calculator", "label": _("Price Calculator")},
            ],
        }
    ]


