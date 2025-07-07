# Copyright (c) 2025, Sushant and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    filters = filters or {}

    columns = [
        {"label": "WO Count ID", "fieldname": "wo_count_id", "fieldtype": "Link", "options": "WO Count", "width": 150},
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
        {"label": "Department", "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 150},
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
        {"label": "Job Card No.", "fieldname": "job_card_reference", "fieldtype": "Link", "options": "Job Card", "width": 150},
        {"label": "Production Plan", "fieldname": "production_plan", "fieldtype": "Link", "options": "Production Plan", "width": 150},
        {"label": "Production Item", "fieldname": "production_item", "fieldtype": "Data", "width": 150},
        {"label": "Operation", "fieldname": "operation", "fieldtype": "Link", "options": "Operation", "width": 150},
        {"label": "Completed Qty", "fieldname": "insert_completed_qty", "fieldtype": "Float", "width": 120},
        {"label": "Operation Rate", "fieldname": "operation_rate", "fieldtype": "Currency", "width": 120},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 120},
    ]

    conditions = "1=1"
    if filters.get("employee"):
        conditions += " AND parent.employee = %(employee)s"
    if filters.get("production_plan"):
        conditions += " AND child.production_plan = %(production_plan)s"
    if filters.get("operation"):
        conditions += " AND child.operation_name = %(operation)s"
    if filters.get("department"):
        conditions += " AND parent.department = %(department)s"
    if filters.get("production_item"):
        conditions += " AND child.production_item = %(production_item)s"

    # ✅ Only show items with job_card_reference
    conditions += " AND child.job_card_reference IS NOT NULL AND child.job_card_reference <> ''"

    query = f"""
        SELECT
            parent.name AS wo_count_id,
            parent.employee,
            emp.employee_name,
            parent.department,
            parent.posting_date,
            child.job_card_reference,
            child.production_plan,
            child.production_item,
            child.operation_name AS operation,
            child.insert_completed_qty,
            parent.operation_rate,
            (child.insert_completed_qty * parent.operation_rate) AS amount
        FROM
            `tabWO Count` AS parent
        JOIN
            `tabWO Count Item` AS child ON child.parent = parent.name
        LEFT JOIN
            `tabEmployee` AS emp ON emp.name = parent.employee
        WHERE
            parent.docstatus = 1
            AND parent.posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND parent.company = 'SUVIDHI FASHION'
            AND {conditions}
    """

    if filters.get("grp_by_emp"):
        query += " ORDER BY parent.employee, parent.posting_date"
    else:
        query += " ORDER BY parent.posting_date"

    result = frappe.db.sql(query, filters, as_dict=True)

    if filters.get("grp_by_emp"):
        grouped_result = []
        current_employee = None
        current_employee_name = ""
        total_qty = 0
        total_amount = 0

        for row in result:
            if row["employee"] != current_employee:
                if current_employee:
                    grouped_result.append({
                        "wo_count_id": None,
                        "employee": current_employee,
                        "employee_name": f"<b>{current_employee_name}</b>",
                        "department": None,
                        "posting_date": None,
                        "job_card_reference": None,
                        "production_plan": None,
                        "production_item": None,
                        "operation": "Total",
                        "insert_completed_qty": total_qty,
                        "operation_rate": None,
                        "amount": total_amount
                    })
                current_employee = row["employee"]
                current_employee_name = row.get("employee_name") or ""
                total_qty = 0
                total_amount = 0

            total_qty += row.get("insert_completed_qty") or 0
            total_amount += row.get("amount") or 0
            grouped_result.append(row)

        if current_employee:
            grouped_result.append({
                "wo_count_id": None,
                "employee": current_employee,
                "employee_name": f"<b>{current_employee_name}</b>",
                "department": None,
                "posting_date": None,
                "job_card_reference": None,
                "production_plan": None,
                "production_item": None,
                "operation": "Total",
                "insert_completed_qty": total_qty,
                "operation_rate": None,
                "amount": total_amount
            })

        return columns, grouped_result

    return columns, result
