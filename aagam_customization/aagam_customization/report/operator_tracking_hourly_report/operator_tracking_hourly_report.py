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

    fromdate_obj = datetime.strptime(fromdate, "%Y-%m-%d")
    todate_obj = datetime.strptime(todate, "%Y-%m-%d")

    url = f"{STITCH_BASE_URL}/api/integration/operator-tracking-hourly-report"

    headers = {
        "STITCH-KEY": STITCH_API_SECRET_KEY,
        "Content-Type": "application/json"
    }

    columns = [
        {"fieldname": "payroll_enrollment_id", "label": "Payroll ID", "fieldtype": "Data", "width": 120},
        {"fieldname": "operator_name", "label": "Operator Name", "fieldtype": "Data", "width": 150},
        {"fieldname": "date", "label": "Date", "fieldtype": "Date", "width": 120},
        {"fieldname": "operation", "label": "Operation", "fieldtype": "Data", "width": 150},
        {"fieldname": "total_pass_count", "label": "Total Pass Count", "fieldtype": "Int", "width": 120},
        {"fieldname": "earning", "label": "Earning", "fieldtype": "Currency", "width": 120},
        {"fieldname": "rate", "label": "Rate", "fieldtype": "Currency", "width": 100},
    ]

    data_rows = []

    # Step 1: Fetch and display API data
    current_date = fromdate_obj
    while current_date <= todate_obj:
        date_str = current_date.strftime("%Y-%m-%d")
        params = {"date": date_str}

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            frappe.throw(f"API Request Failed for {date_str}: {str(e)}")
        except ValueError:
            frappe.throw(f"Invalid JSON response from API for {date_str}")

        if not isinstance(data, dict):
            frappe.throw(f"Unexpected response format from API for {date_str}: {data}")

        if data.get("status") != "success":
            frappe.throw(data.get("data", {}).get("message", f"Unknown error for {date_str}"))

        report_data = data.get("data", [])
        if isinstance(report_data, list):
            for row in report_data:
                data_rows.append({
                    "payroll_enrollment_id": row.get("employee"),
                    "operator_name": row.get("employee_name"),
                    "date": row.get("date"),
                    "operation": row.get("operation"),
                    "total_pass_count": row.get("total_pass_count"),
                    "earning": row.get("amount"),
                    "rate": row.get("rate")
                })

        current_date += timedelta(days=1)

    # Step 2: Append Earning Sheet data after API data
    earning_sheets = frappe.get_all(
        "Earning Sheet",
        filters={
            "source": "Operator Tracking Hourly Report",
            "date": ["between", [fromdate, todate]]
        },
        fields=["name", "employee", "employee_name", "date"]
    )

    for sheet in earning_sheets:
        child_rows = frappe.get_all(
            "Earning Sheet Type",
            filters={"parent": sheet.name},
            fields=["operation", "total_pass_count", "amount", "rate"]
        )
        for child in child_rows:
            data_rows.append({
                "payroll_enrollment_id": sheet.employee,
                "operator_name": sheet.employee_name,
                "date": sheet.date,
                "operation": child.operation,
                "total_pass_count": child.total_pass_count,
                "earning": child.amount,
                "rate": child.rate
            })

    return columns, data_rows
