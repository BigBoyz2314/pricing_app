from __future__ import annotations

import frappe
from frappe.model.document import Document


class PricingFormula(Document):
    def validate(self):
        self._validate_ranges()
        self._validate_overlap()

    def _validate_ranges(self):
        if self.min_width <= 0 or self.max_width <= 0 or self.min_height <= 0 or self.max_height <= 0:
            frappe.throw("Min/Max width and height must be greater than zero.")
        if self.min_width > self.max_width:
            frappe.throw("Min Width cannot exceed Max Width.")
        if self.min_height > self.max_height:
            frappe.throw("Min Height cannot exceed Max Height.")

    def _validate_overlap(self):
        overlap = frappe.get_all(
            "Pricing Formula",
            filters={
                "item": self.item,
                "name": ("!=", self.name),
                "min_width": ("<=", self.max_width),
                "max_width": (">=", self.min_width),
                "min_height": ("<=", self.max_height),
                "max_height": (">=", self.min_height),
            },
            limit=1,
        )
        if overlap:
            frappe.throw("An overlapping formula range already exists for this item.")


