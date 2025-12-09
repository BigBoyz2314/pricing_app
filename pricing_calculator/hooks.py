from __future__ import annotations

app_name = "pricing_calculator"
app_title = "Pricing Calculator"
app_publisher = "Your Name"
app_description = "Store products, width/height pricing formulas, and generate calculated prices."
app_email = "you@example.com"
app_license = "MIT"

# Includes in <head>
app_include_js = []
app_include_css = []

# Doctype JavaScript
doctype_js = {
    "Calculated Quote": "public/js/calculated_quote.js",
}

override_doctype_class = {}

doc_events = {
    "Calculated Quote": {
        "validate": "pricing_calculator.pricing_calculator.api.validate_dimensions",
        "before_save": "pricing_calculator.pricing_calculator.api.set_calculated_price",
    }
}

override_whitelisted_methods = {}

website_generators = []

after_migrate = "pricing_calculator.pricing_calculator.api.ensure_defaults"


