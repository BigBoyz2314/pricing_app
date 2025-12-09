from __future__ import annotations

import frappe
from frappe import _  # noqa: F401
from frappe.model.document import Document
from frappe.utils import flt

from pricing_calculator.pricing_calculator.utils.pricing_engine import PricingEngine
from pricing_calculator.pricing_calculator.utils.pricing_dataset import (
    get_pricing_data,
    process_pricing_request,
)


@frappe.whitelist()
def calculate_price(item: str, width: float, height: float) -> dict:
    """Public API to calculate price."""
    width = flt(width)
    height = flt(height)
    _assert_positive(width, "Width")
    _assert_positive(height, "Height")

    engine = PricingEngine()
    result = engine.calculate(item=item, width=width, height=height)
    return result


@frappe.whitelist()
def validate_dimensions(doc: Document, _method: str = None):
    _assert_positive(doc.width, "Width")
    _assert_positive(doc.height, "Height")


@frappe.whitelist()
def set_calculated_price(doc: Document, _method: str = None):
    if not doc.selected_item or not doc.width or not doc.height:
        return
    result = calculate_price(doc.selected_item, doc.width, doc.height)
    doc.calculated_price = result.get("price")
    doc.breakdown = result.get("breakdown")


@frappe.whitelist()
def get_pricing_dataset():
    """Return parsed dataset for UI (cached)."""
    return get_pricing_data()


@frappe.whitelist()
def calculate_dataset_price(request: dict):
    """Calculate price using the CSV dataset (SignCalc parity)."""
    payload = frappe.parse_json(request)
    success, data = process_pricing_request(payload)
    if not success:
        frappe.throw(data.get("error") or "Unable to calculate price.")
    return data


@frappe.whitelist()
def create_quotation(customer: dict, items: list):
    """Create a Draft Quotation in ERPNext from the page."""
    customer = frappe.parse_json(customer)
    items = frappe.parse_json(items)

    if not customer.get("name"):
        frappe.throw("Customer name is required.")

    quotation_items = []
    for item in items:
        calc = item.get("calculation") or {}
        inputs = item.get("inputs") or {}
        selection = item.get("selection") or {}
        row = item.get("row") or {}

        desc_parts = [
            selection.get("category"),
            selection.get("size"),
            selection.get("material"),
            selection.get("finish"),
        ]
        dimensions = ""
        if (row.get("unit") or "").lower() == "sq/m":
            dimensions = f"{inputs.get('height', 0)}mm x {inputs.get('width', 0)}mm"
        description = ", ".join([p for p in desc_parts if p and p != "Zero"])
        if dimensions:
            description = f"{description} ({dimensions})"

        quotation_items.append(
            {
                "item_code": "Service",
                "item_name": description or "Custom Item",
                "description": description or "Custom Item",
                "qty": inputs.get("quantity") or 1,
                "rate": calc.get("basePrice") or 0,
                "uom": "Nos",
            }
        )

    quotation = frappe.new_doc("Quotation")
    quotation.quotation_to = "Lead"
    quotation.party_name = customer.get("name")
    quotation.customer_name = customer.get("name")
    quotation.contact_email = customer.get("email")
    quotation.contact_mobile = customer.get("phone")
    quotation.company = frappe.defaults.get_user_default("Company")
    quotation.transaction_date = frappe.utils.nowdate()
    quotation.items = quotation_items
    quotation.notes = customer.get("reference")
    quotation.insert(ignore_permissions=True)
    return quotation.name


def ensure_defaults():
    """Seed defaults if needed."""
    if not frappe.db.exists("Module Def", {"module_name": "Pricing Calculator"}):
        module = frappe.new_doc("Module Def")
        module.module_name = "Pricing Calculator"
        module.app_name = "pricing_calculator"
        module.save(ignore_permissions=True)

    _ensure_price_calculator_page()
    _ensure_price_calculator_workspace()


def _assert_positive(value, label: str):
    if value is None or value <= 0:
        frappe.throw(f"{label} must be greater than zero.")


def _ensure_price_calculator_page():
    """Create a custom Page so desk users can open /app/price-calculator without Developer Mode."""
    if frappe.db.exists("Page", "price_calculator"):
        return

    page = frappe.new_doc("Page")
    page.page_name = "price_calculator"
    page.title = "Price Calculator"
    page.module = "Pricing Calculator"
    page.route = "price-calculator"
    page.standard = 0  # must be non-standard to avoid developer mode
    page.custom = 1
    page.single_page = 1
    # Limit to System Manager by default; admins can broaden via the UI
    page.append("roles", {"role": "System Manager"})
    page.insert(ignore_permissions=True)
    frappe.db.commit()


def _ensure_price_calculator_workspace():
    """Create a custom Workspace with a shortcut to the page."""
    if frappe.db.exists("Workspace", "Pricing Calculator"):
        return

    ws = frappe.new_doc("Workspace")
    ws.name = "Pricing Calculator"
    ws.label = "Pricing Calculator"
    ws.title = "Pricing Calculator"
    ws.module = "Pricing Calculator"
    ws.icon = "octicon octicon-calculator"
    ws.public = 1
    ws.sequence_id = 1
    ws.extendable = 0
    ws.is_hidden = 0
    ws.for_user = ""
    ws.extend = ""
    ws.content = ""
    ws.append(
        "shortcuts",
        {
            "type": "Page",
            "label": "Price Calculator",
            "link_to": "price_calculator",
        },
    )
    ws.insert(ignore_permissions=True)
    frappe.db.commit()


