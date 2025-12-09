/* eslint-disable no-undef */
frappe.pages["price_calculator"].on_page_load = async function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "Price Calculator",
    single_column: true,
  });

  const app = $(wrapper).find("#pc-app");
  app.html(`<div class="text-muted">Loading pricing data…</div>`);

  try {
    const dataset = await frappe.call({
      method: "pricing_calculator.pricing_calculator.api.get_pricing_dataset",
    });
    build_ui(app, dataset.message || []);
  } catch (e) {
    app.html(`<div class="alert alert-danger">Failed to load pricing data</div>`);
  }
};

function build_ui(root, data) {
  const state = {
    selection: {
      group: "",
      category: "",
      size: "",
      material: "",
      finish: "",
      sides: "",
      variables: "",
    },
    inputs: { height: 0, width: 0, quantity: 1 },
    customer: { name: "", company: "", email: "", phone: "", reference: "" },
    items: [],
    matchedRow: null,
    calc: null,
  };

  const options = {
    groups: uniq(data.map((d) => d.productGroup)),
    categories: [],
    sizes: [],
    materials: [],
    finishes: [],
    sides: [],
    variables: [],
  };

  const template = `
    <div class="row gy-4">
      <div class="col-lg-8">
        <div class="card h-100">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-start mb-3">
              <div>
                <h4 class="mb-0">Product Configuration</h4>
                <div class="text-muted small">Match the SignCalc UI</div>
              </div>
              <span class="badge bg-secondary">Standalone</span>
            </div>
            <div id="pc-filters" class="row gy-3"></div>
            <hr />
            <div id="pc-inputs" class="row gy-3"></div>
          </div>
        </div>
        <div class="card mt-3">
          <div class="card-body bg-dark text-white rounded">
            <div class="d-flex align-items-center justify-content-between">
              <div>
                <div class="text-uppercase small text-muted">Estimated Cost</div>
                <div id="pc-estimate" class="fs-3 fw-bold">Configure to see price</div>
              </div>
              <button class="btn btn-light" id="pc-add" disabled>Add to Quote</button>
            </div>
          </div>
        </div>
        <div class="card mt-3">
          <div class="card-body">
            <h5>Customer Details</h5>
            <div id="pc-customer" class="row gy-3"></div>
          </div>
        </div>
      </div>
      <div class="col-lg-4">
        <div class="card">
          <div class="card-body">
            <h5 class="d-flex justify-content-between align-items-center">
              Quote Items <span class="badge bg-primary" id="pc-count">0</span>
            </h5>
            <div id="pc-items" class="vstack gap-2 mt-2"></div>
            <hr />
            <div id="pc-totals" class="small"></div>
            <div class="d-grid gap-2 mt-3">
              <button class="btn btn-outline-secondary" id="pc-export" disabled>Export PDF</button>
              <button class="btn btn-primary" id="pc-submit" disabled>Submit to ERPNext</button>
              <button class="btn btn-link text-muted" id="pc-reset">Start New Quote</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  root.html(template);

  const filters = $(root).find("#pc-filters");
  const inputs = $(root).find("#pc-inputs");
  const customer = $(root).find("#pc-customer");
  const estimate = $(root).find("#pc-estimate");
  const addBtn = $(root).find("#pc-add");
  const itemsWrap = $(root).find("#pc-items");
  const totalsWrap = $(root).find("#pc-totals");
  const countBadge = $(root).find("#pc-count");
  const exportBtn = $(root).find("#pc-export");
  const submitBtn = $(root).find("#pc-submit");
  const resetBtn = $(root).find("#pc-reset");

  renderFilters(filters, options, state, data, refreshAll);
  renderInputs(inputs, state, refreshCalc);
  renderCustomer(customer, state);

  addBtn.on("click", () => {
    if (!state.calc || !state.matchedRow) return;
    const item = {
      id: crypto.randomUUID(),
      selection: { ...state.selection },
      inputs: { ...state.inputs },
      row: state.matchedRow,
      calculation: state.calc,
    };
    state.items.push(item);
    refreshItems();
  });

  exportBtn.on("click", () => {
    if (!state.items.length) return;
    frappe.msgprint("Use print view to export PDF of the quote.");
  });

  submitBtn.on("click", async () => {
    if (!state.items.length) return;
    if (!state.customer.name) {
      frappe.msgprint("Enter customer name to submit.");
      return;
    }
    submitBtn.prop("disabled", true);
    try {
      const r = await frappe.call({
        method: "pricing_calculator.pricing_calculator.api.create_quotation",
        args: { customer: state.customer, items: state.items },
      });
      frappe.show_alert({ message: `Quotation ${r.message} created`, indicator: "green" });
    } catch (e) {
      frappe.msgprint(e.message || "Failed to create quotation.");
    } finally {
      submitBtn.prop("disabled", false);
    }
  });

  resetBtn.on("click", () => {
    state.items = [];
    state.inputs = { height: 0, width: 0, quantity: 1 };
    state.customer = { name: "", company: "", email: "", phone: "", reference: "" };
    refreshAll();
    renderCustomer(customer, state);
  });

  function refreshAll() {
    options.categories = uniq(
      data.filter((d) => d.productGroup === state.selection.group).map((d) => d.productCategory)
    );

    const filtered = data.filter(
      (d) => d.productGroup === state.selection.group && d.productCategory === state.selection.category
    );
    options.sides = uniq(filtered.map((d) => d.printingSides));
    options.variables = uniq(filtered.map((d) => d.variables));
    options.sizes = uniq(filtered.map((d) => d.size));
    options.materials = uniq(filtered.map((d) => d.material));
    options.finishes = uniq(filtered.map((d) => d.finish));

    filters.empty();
    renderFilters(filters, options, state, data, refreshAll);
    refreshCalc();
  }

  async function refreshCalc() {
    const payload = {
      productGroup: state.selection.group,
      productCategory: state.selection.category,
      options: {
        size: state.selection.size,
        material: state.selection.material,
        finish: state.selection.finish,
        sides: state.selection.sides,
        variables: state.selection.variables,
      },
      dimensions: { heightMm: state.inputs.height, widthMm: state.inputs.width },
      quantity: state.inputs.quantity,
    };

    try {
      const r = await frappe.call({
        method: "pricing_calculator.pricing_calculator.api.calculate_dataset_price",
        args: { request: payload },
      });
      const msg = r.message || {};
      state.matchedRow = msg.row;
      state.calc = msg.calc;
      estimate.text(`£${(msg.grossTotal || 0).toFixed(2)} (incl VAT)`);
      addBtn.prop("disabled", false);
    } catch (e) {
      state.matchedRow = null;
      state.calc = null;
      estimate.text("Configure to see price");
      addBtn.prop("disabled", true);
    }
  }

  function refreshItems() {
    countBadge.text(state.items.length);
    exportBtn.prop("disabled", !state.items.length);
    submitBtn.prop("disabled", !state.items.length);
    itemsWrap.empty();
    let total = 0;
    let vat = 0;
    let gross = 0;

    state.items.forEach((item) => {
      total += item.calculation.total;
      vat += item.calculation.vatAmount;
      gross += item.calculation.totalWithVat;
      const desc = [
        item.selection.category,
        item.selection.size === "Zero" ? null : item.selection.size,
        item.selection.material === "Zero" ? null : item.selection.material,
        item.selection.finish,
      ]
        .filter(Boolean)
        .join(", ");
      itemsWrap.append(`
        <div class="border rounded p-2 d-flex justify-content-between align-items-start">
          <div>
            <div class="fw-semibold">${desc || "Custom item"}</div>
            <div class="text-muted small">Qty: ${item.inputs.quantity}</div>
          </div>
          <div class="text-end">
            <div class="fw-bold">£${item.calculation.total.toFixed(2)}</div>
            <a href="#" data-id="${item.id}" class="text-danger small pc-remove">remove</a>
          </div>
        </div>
      `);
    });

    itemsWrap.find(".pc-remove").on("click", function (e) {
      e.preventDefault();
      const id = $(this).data("id");
      state.items = state.items.filter((i) => i.id !== id);
      refreshItems();
    });

    totalsWrap.html(`
      <div class="d-flex justify-content-between"><span>Subtotal</span><strong>£${total.toFixed(
        2
      )}</strong></div>
      <div class="d-flex justify-content-between text-muted"><span>VAT</span><span>£${vat.toFixed(
        2
      )}</span></div>
      <div class="d-flex justify-content-between fw-bold fs-6 mt-2"><span>Total</span><span>£${gross.toFixed(
        2
      )}</span></div>
    `);
  }
}

function renderFilters(container, options, state, data, refresh) {
  const makeSelect = (id, label, values) => `
    <div class="col-md-6">
      <label class="form-label small fw-semibold">${label}</label>
      <select class="form-select form-select-sm" id="${id}">
        <option value="">Select</option>
        ${values.map((v) => `<option value="${v}">${v || "Standard"}</option>`).join("")}
      </select>
    </div>`;

  container.append(makeSelect("pc-group", "Group", options.groups));
  container.append(makeSelect("pc-category", "Category", options.categories));
  container.append(makeSelect("pc-size", "Size / Thickness", options.sizes));
  container.append(makeSelect("pc-material", "Material", options.materials));
  container.append(makeSelect("pc-variables", "Shape / Variable", options.variables));
  container.append(makeSelect("pc-finish", "Finish", options.finishes));
  container.append(makeSelect("pc-sides", "Printed Sides", options.sides));

  container.find("#pc-group").val(state.selection.group).on("change", (e) => {
    state.selection.group = e.target.value;
    state.selection.category = "";
    refresh();
  });
  container.find("#pc-category").val(state.selection.category).on("change", (e) => {
    state.selection.category = e.target.value;
    refresh();
  });
  container.find("#pc-size").val(state.selection.size).on("change", (e) => {
    state.selection.size = e.target.value;
  });
  container.find("#pc-material").val(state.selection.material).on("change", (e) => {
    state.selection.material = e.target.value;
  });
  container.find("#pc-variables").val(state.selection.variables).on("change", (e) => {
    state.selection.variables = e.target.value;
  });
  container.find("#pc-finish").val(state.selection.finish).on("change", (e) => {
    state.selection.finish = e.target.value;
  });
  container.find("#pc-sides").val(state.selection.sides).on("change", (e) => {
    state.selection.sides = e.target.value;
  });
}

function renderInputs(container, state, refreshCalc) {
  const tpl = `
    <div class="col-md-4">
      <label class="form-label small fw-semibold">Height (mm)</label>
      <input type="number" min="0" class="form-control form-control-sm" id="pc-height" />
    </div>
    <div class="col-md-4">
      <label class="form-label small fw-semibold">Width (mm)</label>
      <input type="number" min="0" class="form-control form-control-sm" id="pc-width" />
    </div>
    <div class="col-md-4">
      <label class="form-label small fw-semibold">Quantity</label>
      <input type="number" min="1" class="form-control form-control-sm" id="pc-qty" value="1" />
    </div>
  `;
  container.html(tpl);

  container.find("#pc-height").val(state.inputs.height).on("input", (e) => {
    state.inputs.height = parseFloat(e.target.value || 0);
    refreshCalc();
  });
  container.find("#pc-width").val(state.inputs.width).on("input", (e) => {
    state.inputs.width = parseFloat(e.target.value || 0);
    refreshCalc();
  });
  container.find("#pc-qty").val(state.inputs.quantity).on("input", (e) => {
    state.inputs.quantity = parseFloat(e.target.value || 1);
    refreshCalc();
  });
}

function renderCustomer(container, state) {
  const fields = [
    ["name", "Full Name"],
    ["company", "Company"],
    ["email", "Email"],
    ["phone", "Phone"],
    ["reference", "Reference / Notes"],
  ];
  const html = fields
    .map(
      ([key, label]) => `
    <div class="col-md-6">
      <label class="form-label small fw-semibold">${label}</label>
      <input type="text" class="form-control form-control-sm" id="pc-c-${key}" value="${state.customer[key] || ""}" />
    </div>
  `
    )
    .join("");
  container.html(html);
  fields.forEach(([key]) => {
    container.find(`#pc-c-${key}`).on("input", (e) => {
      state.customer[key] = e.target.value;
    });
  });
}

function uniq(arr) {
  return Array.from(new Set(arr.filter(Boolean)));
}


