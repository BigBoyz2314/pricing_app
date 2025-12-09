from __future__ import annotations

import frappe
from frappe.model.document import Document


class PricingItem(Document):
    def validate(self):
        if not self.active:
            return
        existing = frappe.get_all(
            "Pricing Item", filters={"item_name": self.item_name, "name": ("!=", self.name)}
        )
        if existing:
            frappe.throw("Item Name must be unique.")


