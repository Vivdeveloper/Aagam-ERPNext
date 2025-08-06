import frappe

def execute(filters=None):
    filters = filters or {}

    columns = [
        {"label": "Job Card No.", "fieldname": "job_card_reference", "fieldtype": "Link", "options": "Job Card", "width": 150},
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Data", "width": 120},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
        {"label": "Department", "fieldname": "department", "fieldtype": "Data", "width": 150},
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
        {"label": "WO Count ID", "fieldname": "wo_count_id", "fieldtype": "Link", "options": "WO Count", "width": 150},
        {"label": "Production Plan", "fieldname": "production_plan", "fieldtype": "Link", "options": "Production Plan", "width": 150},
        {"label": "Production Item", "fieldname": "production_item", "fieldtype": "Data", "width": 150},
        {"label": "Operation", "fieldname": "operation", "fieldtype": "Data", "width": 150},
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

    conditions += " AND child.job_card_reference IS NOT NULL AND child.job_card_reference <> ''"

    query = f"""
        SELECT
            child.job_card_reference,
            parent.employee,
            emp.employee_name,
            parent.department,
            parent.posting_date,
            parent.name AS wo_count_id,
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

    # 🔄 Fetch Earning Sheet data
    earning_data = frappe.db.sql("""
        SELECT
            NULL AS job_card_reference,
            es.employee,
            emp.employee_name,
            NULL AS department,
            es.date AS posting_date,
            es.name AS wo_count_id,
            NULL AS production_plan,
            NULL AS production_item,
            est.operation,
            NULL AS insert_completed_qty,
            NULL AS operation_rate,
            est.amount
        FROM
            `tabEarning Sheet` es
        JOIN
            `tabEarning Sheet Type` est ON est.parent = es.name
        LEFT JOIN
            `tabEmployee` emp ON emp.name = es.employee
        WHERE
            es.docstatus = 1
            AND es.date BETWEEN %(from_date)s AND %(to_date)s
            AND es.company = 'SUVIDHI FASHION'
    """, filters, as_dict=True)

    result.extend(earning_data)

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
                        "job_card_reference": None,
                        "employee": current_employee,
                        "employee_name": f"{current_employee_name}",
                        "department": None,
                        "posting_date": None,
                        "wo_count_id": None,
                        "production_plan": None,
                        "production_item": None,
                        "operation": "<b>Total</b>",
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
                "job_card_reference": None,
                "employee": current_employee,
                "employee_name": f"{current_employee_name}",
                "department": None,
                "posting_date": None,
                "wo_count_id": None,
                "production_plan": None,
                "production_item": None,
                "operation": "<b>Total</b>",
                "insert_completed_qty": total_qty,
                "operation_rate": None,
                "amount": total_amount
            })

        return columns, grouped_result

    return columns, result

