import requests
import frappe
from datetime import datetime, timedelta

STITCH_BASE_URL = "http://portal2.stitcherp.com"
STITCH_API_SECRET_KEY = "674eea38-f7a7-45d5-8317-d6295287b125"

def execute(filters=None):
    if not filters or not filters.get("fromdate") or not filters.get("todate"):
        frappe.throw("From Date and To Date filters are required")

    fromdate = filters.get("fromdate")
    todate = filters.get("todate")
    group_by_employee = filters.get("group_by_employee", False)

    fromdate_obj = datetime.strptime(fromdate, "%Y-%m-%d")
    todate_obj = datetime.strptime(todate, "%Y-%m-%d")

    url = f"{STITCH_BASE_URL}/api/integration/operator-tracking-hourly-report"

    headers = {
        "STITCH-KEY": STITCH_API_SECRET_KEY,
        "Content-Type": "application/json"
    }

    columns = [
        {"fieldname": "operator_id", "label": "Operator ID", "fieldtype": "Data", "width": 100},
        {"fieldname": "payroll_enrollment_id", "label": "Payroll ID", "fieldtype": "Data", "width": 120},
        {"fieldname": "operator_name", "label": "Operator Name", "fieldtype": "Data", "width": 150},
        {"fieldname": "name", "label": "Name", "fieldtype": "Data", "width": 150},
        {"fieldname": "style_name", "label": "Style Name", "fieldtype": "Data", "width": 150},
        {"fieldname": "style_id", "label": "Style ID", "fieldtype": "Data", "width": 100},
        {"fieldname": "date", "label": "Date", "fieldtype": "Date", "width": 120},
        {"fieldname": "operation", "label": "Operation", "fieldtype": "Data", "width": 150},
        {"fieldname": "total_pass_count", "label": "Total Pass Count", "fieldtype": "Int", "width": 120},
        {"fieldname": "earning", "label": "Earning", "fieldtype": "Currency", "width": 120},
        {"fieldname": "rate", "label": "Rate", "fieldtype": "Currency", "width": 100},
    ]

    data_rows = []

    employee_map = {}  # group rows per employee

    current_date = fromdate_obj
    while current_date <= todate_obj:
        date_str = current_date.strftime("%Y-%m-%d")
        params = {"date": date_str}

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            frappe.throw(f"API Request Failed for {date_str}: {str(e)}")

        data = response.json()

        if data.get("status") != "success":
            frappe.throw(data.get("data", {}).get("message", f"Unknown error for {date_str}"))

        operators = data.get("data", {})

        for operator_id, operator_info in operators.items():
            employee_key = operator_id

            if employee_key not in employee_map:
                employee_map[employee_key] = {
                    "info": operator_info,
                    "rows": [],
                    "total_pass_count": 0,
                    "total_earning": 0,
                    "total_rate": 0
                }

            for style in operator_info.get("styles", []):
                for style_data in style.get("style_data", []):
                    row = {
                        "operator_id": operator_id,
                        "payroll_enrollment_id": operator_info.get("payroll_enrollment_id"),
                        "operator_name": operator_info.get("operator_name"),
                        "name": operator_info.get("name"),
                        "style_name": style.get("style_name"),
                        "style_id": style.get("style_id"),
                        "date": date_str,
                        "operation": style_data.get("operation"),
                        "total_pass_count": style_data.get("total_pass_count"),
                        "earning": style_data.get("earning"),
                        "rate": style_data.get("rate"),
                    }

                    employee_map[employee_key]["rows"].append(row)

                    # Accumulate totals
                    employee_map[employee_key]["total_pass_count"] += row["total_pass_count"]
                    employee_map[employee_key]["total_earning"] += row["earning"]
                    employee_map[employee_key]["total_rate"] += row["rate"]

        current_date += timedelta(days=1)

    # After gathering all rows, insert per-employee rows + total
    for emp_id, emp_data in employee_map.items():
        # Add individual rows
        data_rows.extend(emp_data["rows"])

        if group_by_employee:
            # Add total row after each employee's rows
            operator_info = emp_data["info"]
            total_row = {
                "operator_id": f"<b>{emp_id}</b>",
                "payroll_enrollment_id": f"<b>{operator_info.get('payroll_enrollment_id')}</b>",
                "operator_name": f"<b>{operator_info.get('operator_name')}</b>",
                "name": f"<b>{operator_info.get('name')}</b>",
                "style_name": "<b>TOTAL</b>",
                "style_id": "-",
                "date": "-",
                "operation": "<b>TOTAL</b>",
                "total_pass_count": emp_data["total_pass_count"],
                "earning": emp_data["total_earning"],
                "rate": emp_data["total_rate"],
            }
            data_rows.append(total_row)

    return columns, data_rows
