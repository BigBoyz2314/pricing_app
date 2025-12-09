from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import frappe

DATA_FILE = Path(__file__).resolve().parent.parent / "constants" / "pricing_data.csv"


def _parse_currency(value: str) -> float:
    value = (value or "").replace("£", "").replace(",", "").strip()
    return float(value) if value else 0.0


def _parse_percentage(value: str) -> float:
    value = (value or "").replace("%", "").strip()
    return float(value) / 100 if value else 0.0


def _make_id(idx: int) -> str:
    return f"row-{idx}"


@lru_cache(maxsize=1)
def get_pricing_data() -> List[dict]:
    if not DATA_FILE.exists():
        frappe.throw("Pricing data file missing.")

    rows: List[dict] = []
    with open(DATA_FILE, encoding="utf-8") as f:
        reader = csv.reader(f)
        # skip header
        next(reader, None)
        for idx, cols in enumerate(reader, start=1):
            if len(cols) < 15:
                continue
            rows.append(
                {
                    "id": _make_id(idx),
                    "productGroup": cols[0],
                    "productCategory": cols[1],
                    "printingSides": cols[2],
                    "variables": cols[3],
                    "size": cols[4],
                    "material": cols[5],
                    "finish": cols[6],
                    "taxRate": _parse_percentage(cols[8]),
                    "unitPrice": _parse_currency(cols[9]),
                    "unit": cols[10],
                    "inkCost": _parse_currency(cols[11]),
                    "sheetCost": _parse_currency(cols[12]),
                    "laminationCost": _parse_currency(cols[13]),
                    "orCost": _parse_currency(cols[14]),
                }
            )
    return rows


def distinct(field: str, data: Optional[Iterable[dict]] = None) -> List[str]:
    data = data or get_pricing_data()
    values = sorted({(row.get(field) or "").strip() for row in data if row.get(field)})
    return values


def find_product(
    data: List[dict],
    group: str,
    category: str,
    *,
    size: str = "",
    material: str = "",
    finish: str = "",
    sides: str = "",
    variables: str = "",
) -> Optional[dict]:
    for row in data:
        if row["productGroup"] != group or row["productCategory"] != category:
            continue
        if sides and row["printingSides"] != sides:
            continue
        if variables and row["variables"] != variables:
            continue
        if size and row["size"] != size:
            continue
        if material and row["material"] != material:
            continue
        if finish and row["finish"] != finish:
            continue
        return row
    return None


def calculate_price(row: dict, quantity: float, height_mm: float = 0, width_mm: float = 0) -> dict:
    unit = row.get("unit") or ""
    area_m2 = 0
    base_price = 0
    total = 0

    if unit.lower() == "sq/m":
        area_m2 = (height_mm / 1000) * (width_mm / 1000)
        base_price = area_m2 * float(row["unitPrice"])
    else:
        base_price = float(row["unitPrice"])

    total = base_price * quantity
    vat_amount = total * float(row["taxRate"])
    total_with_vat = total + vat_amount

    return {
        "basePrice": base_price,
        "total": total,
        "vatAmount": vat_amount,
        "totalWithVat": total_with_vat,
        "areaM2": area_m2 if unit.lower() == "sq/m" else None,
    }


def process_pricing_request(payload: dict) -> Tuple[bool, dict]:
    data = get_pricing_data()
    group = payload.get("productGroup")
    category = payload.get("productCategory")
    options = payload.get("options") or {}
    quantity = float(payload.get("quantity") or 0)
    dims = payload.get("dimensions") or {}
    height = float(dims.get("heightMm") or 0)
    width = float(dims.get("widthMm") or 0)

    row = find_product(
        data,
        group,
        category,
        size=options.get("size") or "",
        material=options.get("material") or "",
        finish=options.get("finish") or "",
        sides=options.get("sides") or "",
        variables=options.get("variables") or "",
    )

    if not row:
        return False, {"error": "Product configuration not found."}

    if (row.get("unit") or "").lower() == "sq/m" and (not height or not width):
        return False, {"error": "Height and Width are required for this item."}

    calc = calculate_price(row, quantity, height, width)

    return True, {
        "unitPrice": calc["basePrice"],
        "netTotal": calc["total"],
        "vatTotal": calc["vatAmount"],
        "grossTotal": calc["totalWithVat"],
        "currency": "GBP",
        "breakdown": {"unit": row["unit"], "areaM2": calc["areaM2"], "rate": row["unitPrice"]},
        "meta": {
            "productId": row["id"],
            "description": f"{row['productCategory']} - {row['size']} {row['material']}",
        },
        "row": row,
        "calc": calc,
    }


