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

    employee_map = {}

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
                }

            for entry in operator_info.get("details", []):
                row = {
                    "operator_id": operator_id,
                    "payroll_enrollment_id": operator_info.get("employee"),
                    "operator_name": operator_info.get("employee_name"),
                    "name": "",  # from API not available
                    "style_name": entry.get("style_name"),
                    "style_id": entry.get("style_id"),
                    "date": entry.get("date"),
                    "operation": entry.get("operation"),
                    "total_pass_count": entry.get("total_pass_count"),
                    "earning": entry.get("amount"),
                    "rate": entry.get("rate"),
                }
                data_rows.append(row)

            # Now pull matching Earning Sheet records
            employee = operator_info.get("employee")
            employee_name = operator_info.get("employee_name")
            date = operator_info.get("date")

            if employee and employee_name and date:
                earning_sheets = frappe.get_all(
                    "Earning Sheet",
                    filters={
                        "payroll_enrollment_id": employee,
                        "operator_name": employee_name,
                        "date": date,
                        "source": "Operator Tracking Hourly Report"
                    },
                    fields=["name"]
                )

                for es in earning_sheets:
                    es_doc = frappe.get_doc("Earning Sheet", es.name)
                    for child in es_doc.earning_sheet_type:
                        data_rows.append({
                            "operator_id": operator_id,
                            "payroll_enrollment_id": employee,
                            "operator_name": employee_name,
                            "name": es_doc.name,
                            "style_name": "",  # not available in Earning Sheet
                            "style_id": "",    # not available in Earning Sheet
                            "date": date,
                            "operation": child.operation,
                            "total_pass_count": child.total_pass_count,
                            "earning": child.amount,
                            "rate": child.rate,
                        })

        current_date += timedelta(days=1)

    return columns, data_rows
