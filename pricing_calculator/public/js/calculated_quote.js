frappe.ui.form.on("Calculated Quote", {
  refresh(frm) {
    frm.add_custom_button("Calculate Price", () => calculate(frm));
  },
  width(frm) {
    validate_positive(frm, "width", "Width");
  },
  height(frm) {
    validate_positive(frm, "height", "Height");
  },
});

function validate_positive(frm, fieldname, label) {
  const value = frm.doc[fieldname];
  if (value && value <= 0) {
    frappe.msgprint(`${label} must be greater than zero.`);
  }
}

function calculate(frm) {
  if (!frm.doc.selected_item || !frm.doc.width || !frm.doc.height) {
    frappe.msgprint("Please fill Item, Width and Height.");
    return;
  }
  frappe.call({
    method: "pricing_calculator.pricing_calculator.api.calculate_price",
    args: {
      item: frm.doc.selected_item,
      width: frm.doc.width,
      height: frm.doc.height,
    },
    freeze: true,
    callback: (r) => {
      if (!r.message) return;
      frm.set_value("calculated_price", r.message.price);
      frm.set_value("breakdown", r.message.breakdown);
      frm.save_or_update();
    },
  });
}


