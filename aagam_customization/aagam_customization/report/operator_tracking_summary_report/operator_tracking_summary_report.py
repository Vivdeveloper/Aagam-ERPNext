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
    group_by_employee = filters.get("group_by_employee", False)  # Check if the group_by_employee is ticked

    fromdate_obj = datetime.strptime(fromdate, "%Y-%m-%d")
    todate_obj = datetime.strptime(todate, "%Y-%m-%d")

    url = f"{STITCH_BASE_URL}/api/integration/operator-tracking-summary-report"

    headers = {
        "STITCH-KEY": STITCH_API_SECRET_KEY,
        "Content-Type": "application/json"
    }

    columns = [
        {"fieldname": "operator_id", "label": "Operator ID", "fieldtype": "Data", "width": 100},
        {"fieldname": "payroll_enrollment_id", "label": "Payroll ID", "fieldtype": "Data", "width": 120},
        {"fieldname": "operator_name", "label": "Operator Name", "fieldtype": "Data", "width": 150},
        {"fieldname": "name", "label": "Name", "fieldtype": "Data", "width": 150},
        {"fieldname": "style_id", "label": "Style ID", "fieldtype": "Data", "width": 100},
        {"fieldname": "style_name", "label": "Style Name", "fieldtype": "Data", "width": 150},
        {"fieldname": "date", "label": "Date", "fieldtype": "Date", "width": 120},
        {"fieldname": "operation", "label": "Operation", "fieldtype": "Data", "width": 150},
        {"fieldname": "rate", "label": "Rate", "fieldtype": "Currency", "width": 100},
        {"fieldname": "total_pass_count", "label": "Total Production", "fieldtype": "Int", "width": 120},
        {"fieldname": "earning", "label": "Earning", "fieldtype": "Currency", "width": 120},
        
    ]

    data_rows = []
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

        if group_by_employee:
            last_employee = None
            employee_total = None

            for operator_id, operator_info in operators.items():
                current_employee = (operator_id, operator_info.get("payroll_enrollment_id"), 
                                    operator_info.get("operator_name"), operator_info.get("name"))

                # If it's a new employee, add the total row for the previous one
                if last_employee and last_employee != current_employee and employee_total:
                    data_rows.append(employee_total)
                    employee_total = None  # Reset for the new employee

                last_employee = current_employee

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
                            "operation": style_data.get("operation_name"),
                            "total_pass_count": style_data.get("total_production"),
                            "earning": style_data.get("earning"),
                            "rate": style_data.get("rate"),
                        }

                        data_rows.append(row)

                        # Initialize total row if not set
                        if not employee_total:
                            employee_total = {
                                "operator_id": f"<b>{operator_id}</b>",
                                "payroll_enrollment_id": f"<b>{operator_info.get('payroll_enrollment_id')}</b>",
                                "operator_name": f"<b>{operator_info.get('operator_name')}</b>",
                                "name": f"<b>{operator_info.get('name')}</b>",
                                "style_name": "<b>TOTAL</b>",
                                "style_id": "-",
                                "date": "-",
                                "operation": "<b>TOTAL</b>",
                                "total_pass_count": 0,
                                "earning": 0,
                                "rate": 0,
                            }

                        # Accumulate totals
                        employee_total["total_pass_count"] += row["total_pass_count"]
                        employee_total["earning"] += row["earning"]
                        employee_total["rate"] += row["rate"]

            # Insert the last employee's total row
            if employee_total:
                data_rows.append(employee_total)
        else:
            for operator_id, operator_info in operators.items():
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
                            "operation": style_data.get("operation_name"),
                            "total_pass_count": style_data.get("total_production"),
                            "earning": style_data.get("earning"),
                            "rate": style_data.get("rate"),
                        }

                        data_rows.append(row)

        current_date += timedelta(days=1)

    return columns, data_rows
