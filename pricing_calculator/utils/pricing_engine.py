from __future__ import annotations

import frappe
from frappe.utils.safe_exec import safe_exec


class PricingEngine:
    """Encapsulate pricing lookup and calculation logic."""

    def __init__(self):
        self.debug = False

    def calculate(self, item: str, width: float, height: float) -> dict:
        formula = self._get_formula(item, width, height)
        area = width * height
        base_total = (area * (formula.price_per_sqft or 0)) + (formula.fixed_cost or 0)

        breakdown_lines = [
            f"Item: {item}",
            f"Width x Height: {width} x {height}",
            f"Area: {area}",
            f"Price per sqft: {formula.price_per_sqft}",
            f"Fixed cost: {formula.fixed_cost}",
        ]

        total = base_total

        if formula.formula_code:
            total, custom_lines = self._execute_custom_code(
                formula.formula_code,
                context={"width": width, "height": height, "area": area, "base_total": base_total},
            )
            if custom_lines:
                breakdown_lines.extend(custom_lines)

        breakdown_lines.append(f"Total: {total}")

        return {
            "price": total,
            "breakdown": "\n".join(breakdown_lines),
            "area": area,
            "formula_name": formula.name,
        }

    def _get_formula(self, item: str, width: float, height: float):
        formula = frappe.get_all(
            "Pricing Formula",
            filters={
                "item": item,
                "min_width": ("<=", width),
                "max_width": (">=", width),
                "min_height": ("<=", height),
                "max_height": (">=", height),
            },
            fields=["name", "price_per_sqft", "fixed_cost", "formula_code"],
            limit=1,
        )
        if not formula:
            frappe.throw("No pricing formula found for these dimensions.")
        return frappe._dict(formula[0])

    def _execute_custom_code(self, code: str, context: dict) -> tuple[float, list[str]]:
        """Run custom code safely using frappe.safe_exec."""
        exec_context = {}
        safe_exec(code, _locals=exec_context, _globals=context)

        custom_total = exec_context.get("total", context.get("base_total"))
        custom_lines = exec_context.get("breakdown_lines", [])
        if custom_total is None:
            custom_total = context.get("base_total")
        if custom_lines and not isinstance(custom_lines, list):
            custom_lines = [str(custom_lines)]
        return custom_total, [str(line) for line in custom_lines or []]


