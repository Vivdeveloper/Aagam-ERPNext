# Copyright (c) 2025, Sushant and contributors
# For license information, please see license.txt

# import frappe

import frappe
from frappe.utils import getdate

def execute(filters=None):
    filters = filters or {}
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")

    columns = get_columns()
    data = get_data(from_date, to_date)
    chart = make_chart(data)
    report_summary = make_summary(data)

    return columns, data, None, chart, report_summary


def get_columns():
    return [
        {
            "label": "Production Plan",
            "fieldname": "production_plan",
            "fieldtype": "Link",
            "options": "Production Plan",
            "width": 160,
        },
        {
            "label": "Company",
            "fieldname": "company",
            "fieldtype": "Link",
            "options": "Company",
            "width": 140,
        },
        {
            "label": "Workstation",
            "fieldname": "workstation",
            "fieldtype": "Link",
            "options": "Workstation",
            "width": 140,
        },
        {
            "label": "Style",
            "fieldname": "style",
            "fieldtype": "Link",
            "options": "Item",
            "width": 250,
        },
        {
            "label": "Variant Of",
            "fieldname": "variant_of",
            "fieldtype": "Link",
            "options": "Item",
            "width": 240,
        },
        {
            "label": "Planned Qty",
            "fieldname": "planned_qty",
            "fieldtype": "Float",
            "width": 120,
            "precision": "Quantity",
        },
        {
            "label": "Actual Qty",
            "fieldname": "actual_qty",
            "fieldtype": "Float",
            "width": 120,
            "precision": "Quantity",
        },
        {
            "label": "Status",
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 120,
        },
    ]


def get_data(from_date=None, to_date=None):
    # Build filters safely
    conditions = ["p.docstatus < 2"]
    params = {}

    if from_date:
        conditions.append("p.posting_date >= %(from_date)s")
        params["from_date"] = getdate(from_date)
    if to_date:
        conditions.append("p.posting_date <= %(to_date)s")
        params["to_date"] = getdate(to_date)

    where_clause = " AND ".join(conditions)

    # Query: parent = WO Count, child = WO Count Item, plus Item + Production Plan for extra fields
    # Field names based on your description:
    # - child.production_plan
    # - child.production_item
    # - child.qty
    # - child.insert_completed_qty
    # - parent.company
    # - parent.workstation
    # - parent.posting_date
    # - Item.variant_of
    # - Production Plan.status
    rows = frappe.db.sql(
        f"""
        SELECT
            c.production_plan                                   AS production_plan,
            p.company                                           AS company,
            p.workstation                                       AS workstation,
            c.production_item                                   AS style,
            i.variant_of                                        AS variant_of,
            IFNULL(c.qty, 0)                                    AS planned_qty,
            IFNULL(c.insert_completed_qty, 0)                   AS actual_qty,
            pp.status                                           AS status
        FROM `tabWO Count` p
        INNER JOIN `tabWO Count Item` c
            ON c.parent = p.name AND c.parenttype = 'WO Count'
        LEFT JOIN `tabItem` i
            ON i.name = c.production_item
        LEFT JOIN `tabProduction Plan` pp
            ON pp.name = c.production_plan
        WHERE {where_clause}
        ORDER BY p.posting_date DESC, p.name DESC
        """,
        params,
        as_dict=True,
    )

    return rows


def make_chart(rows):
    # Aggregate by company
    by_company = {}
    for r in rows:
        comp = r.get("company") or "Unknown"
        agg = by_company.setdefault(comp, {"planned": 0.0, "actual": 0.0})
        agg["planned"] += float(r.get("planned_qty") or 0)
        agg["actual"] += float(r.get("actual_qty") or 0)

    labels = list(by_company.keys())
    planned = [by_company[c]["planned"] for c in labels]
    actual = [by_company[c]["actual"] for c in labels]

    # ERPNext chart spec
    chart = {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": "Planned Qty", "values": planned},
                {"name": "Actual Qty", "values": actual},
            ],
        },
        "type": "bar",
        "axisOptions": {"xIsSeries": 1},
        "barOptions": {"stacked": 0},  # side-by-side
    }
    return chart


def make_summary(rows):
    total_planned = sum(float(r.get("planned_qty") or 0) for r in rows)
    total_actual = sum(float(r.get("actual_qty") or 0) for r in rows)
    return [
        {
            "label": "Total Planned Qty",
            "value": frappe.utils.fmt_money(total_planned, currency=None, precision=0),
            "indicator": "blue",
        },
        {
            "label": "Total Actual Qty",
            "value": frappe.utils.fmt_money(total_actual, currency=None, precision=0),
            "indicator": "green",
        },
    ]
