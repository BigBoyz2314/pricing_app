# Pricing Calculator

Custom Frappe app to manage pricing formulas and calculate item quotes by width and height.

## Features
- Doctypes: Pricing Item, Pricing Formula, Calculated Quote
- Pricing engine with safe custom formula execution (`formula_code`)
- Desk/web page "Price Calculator" for quick calculations
- Client scripts to calculate and store quotes

## Install
```bash
bench get-app pricing_calculator https://github.com/myuser/pricing_calculator
bench install-app pricing_calculator
```

## Development
- Compatible with Frappe Cloud (no server-level deps)
- Key server API: `pricing_calculator.pricing_calculator.api.calculate_price`


