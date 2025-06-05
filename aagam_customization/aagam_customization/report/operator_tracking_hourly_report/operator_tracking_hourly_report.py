import frappe
from datetime import datetime, timedelta
import requests

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

    employee_map = {}
    data_rows = []

    # Fetch data from API day by day
    for date in (fromdate_obj + timedelta(n) for n in range((todate_obj - fromdate_obj).days + 1)):
        date_str = date.strftime("%Y-%m-%d")
        params = {
            "date": date_str
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            frappe.throw(f"API Request Failed for {date_str}: {str(e)}")

        data = response.json()
        if data.get("status") != "success":
            frappe.throw(data.get("data", {}).get("message", f"Unknown error for {date_str}"))

        operators = data.get("data", {}).get("operators", [])
        for op in operators:
            row = {
                "payroll_enrollment_id": op.get("payroll_enrollment_id"),
                "operator_name": op.get("operator_name"),
                "name": op.get("name"),
                "date": date_str,
                "operation": op.get("operation"),
                "total_pass_count": op.get("total_pass_count"),
                "earning": op.get("earning"),
                "rate": op.get("rate")
            }
            data_rows.append(row)

            if group_by_employee:
                emp_id = op.get("payroll_enrollment_id")
                if emp_id not in employee_map:
                    employee_map[emp_id] = {
                        "info": {
                            "payroll_enrollment_id": op.get("payroll_enrollment_id"),
                            "operator_name": op.get("operator_name"),
                            "name": op.get("name")
                        },
                        "rows": [],
                        "total_pass_count": 0,
                        "total_earning": 0,
                        "total_rate": 0
                    }

                employee_map[emp_id]["rows"].append(row)
                employee_map[emp_id]["total_pass_count"] += op.get("total_pass_count") or 0
                employee_map[emp_id]["total_earning"] += op.get("earning") or 0
                employee_map[emp_id]["total_rate"] += op.get("rate") or 0

    # Append Earning Sheet Data
    earning_sheets = frappe.get_all(
        "Earning Sheet",
        filters={"date": ["between", [fromdate, todate]]},
        fields=["name", "employee", "employee_name", "date"]
    )

    for sheet in earning_sheets:
        child_rows = frappe.get_all(
            "Earning Sheet Type",
            filters={"parent": sheet.name},
            fields=["operation", "total_pass_count", "amount", "rate"]
        )
        for child in child_rows:
            row = {
                "payroll_enrollment_id": sheet.employee,
                "operator_name": sheet.employee_name,
                "name": sheet.employee_name,
                "date": sheet.date,
                "operation": child.operation,
                "total_pass_count": child.total_pass_count,
                "earning": child.amount,
                "rate": child.rate
            }
            data_rows.append(row)

            if group_by_employee:
                emp_id = sheet.employee
                if emp_id not in employee_map:
                    employee_map[emp_id] = {
                        "info": {
                            "payroll_enrollment_id": sheet.employee,
                            "operator_name": sheet.employee_name,
                            "name": sheet.employee_name
                        },
                        "rows": [],
                        "total_pass_count": 0,
                        "total_earning": 0,
                        "total_rate": 0
                    }

                employee_map[emp_id]["rows"].append(row)
                employee_map[emp_id]["total_pass_count"] += child.total_pass_count or 0
                employee_map[emp_id]["total_earning"] += child.amount or 0
                employee_map[emp_id]["total_rate"] += child.rate or 0

    # Build final dataset
    final_rows = []

    if group_by_employee:
        for emp_id, emp_data in employee_map.items():
            final_rows.extend(emp_data["rows"])
            final_rows.append({
                "payroll_enrollment_id": "",
                "operator_name": "",
                "name": f"Total for {emp_data['info']['name']}",
                "date": "",
                "operation": "",
                "total_pass_count": emp_data["total_pass_count"],
                "earning": emp_data["total_earning"],
                "rate": emp_data["total_rate"]
            })
    else:
        final_rows = data_rows

    columns = [
        {"label": "Payroll Enrollment ID", "fieldname": "payroll_enrollment_id", "fieldtype": "Data", "width": 150},
        {"label": "Operator Name", "fieldname": "operator_name", "fieldtype": "Data", "width": 150},
        {"label": "Employee Name", "fieldname": "name", "fieldtype": "Data", "width": 150},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": "Operation", "fieldname": "operation", "fieldtype": "Data", "width": 150},
        {"label": "Pass Count", "fieldname": "total_pass_count", "fieldtype": "Int", "width": 100},
        {"label": "Earning", "fieldname": "earning", "fieldtype": "Currency", "width": 100},
        {"label": "Rate", "fieldname": "rate", "fieldtype": "Currency", "width": 100}
    ]

    return columns, final_rows
