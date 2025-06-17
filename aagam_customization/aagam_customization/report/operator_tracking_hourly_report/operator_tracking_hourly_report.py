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
    payroll_enrollment_id = filters.get("payroll_enrollment_id")

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

    unified_map = {}

    # Fetch Stitch API data
    current_date = fromdate_obj
    while current_date <= todate_obj:
        date_str = current_date.strftime("%Y-%m-%d")
        try:
            response = requests.get(url, headers=headers, params={"date": date_str})
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            frappe.throw(f"API Request Failed for {date_str}: {str(e)}")

        data = response.json()
        if data.get("status") != "success":
            frappe.throw(data.get("data", {}).get("message", f"Unknown error for {date_str}"))

        for operator_id, operator_info in data.get("data", {}).items():
            key = operator_info.get("payroll_enrollment_id")
            if not key or (payroll_enrollment_id and key != payroll_enrollment_id):
                continue

            if key not in unified_map:
                unified_map[key] = {
                    "info": {
                        "payroll_enrollment_id": key,
                        "operator_name": operator_info.get("operator_name"),
                        "name": operator_info.get("name"),
                        "operator_id": operator_id,
                    },
                    "rows": [],
                    "total_pass_count": 0,
                    "total_earning": 0,
                    "total_rate": 0
                }

            for style in operator_info.get("styles", []):
                for style_data in style.get("style_data", []):
                    row = {
                        "operator_id": operator_id,
                        "payroll_enrollment_id": key,
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
                    unified_map[key]["rows"].append(row)
                    unified_map[key]["total_pass_count"] += row["total_pass_count"] or 0
                    unified_map[key]["total_earning"] += row["earning"] or 0
                    unified_map[key]["total_rate"] += row["rate"] or 0

        current_date += timedelta(days=1)

    # Fetch Earning Sheet Data
    earning_sheet_filters = {
        "source": "Operator Tracking Hourly Report",
        "date": ["between", [fromdate, todate]]
    }
    if payroll_enrollment_id:
        earning_sheet_filters["employee"] = payroll_enrollment_id

    sheets = frappe.get_all(
        "Earning Sheet",
        filters=earning_sheet_filters,
        fields=["name", "employee", "employee_name", "date"]
    )

    for sheet in sheets:
        key = sheet.employee
        if key not in unified_map:
            unified_map[key] = {
                "info": {
                    "payroll_enrollment_id": key,
                    "operator_name": sheet.employee_name,
                    "name": sheet.employee_name,
                    "operator_id": key,
                },
                "rows": [],
                "total_pass_count": 0,
                "total_earning": 0,
                "total_rate": 0
            }

        child_rows = frappe.get_all(
            "Earning Sheet Type",
            filters={"parent": sheet.name},
            fields=["operation", "total_pass_count", "amount", "rate"]
        )

        for child in child_rows:
            row = {
                "operator_id": key,
                "payroll_enrollment_id": key,
                "operator_name": sheet.employee_name,
                "name": sheet.employee_name,
                "style_name": "-",
                "style_id": "-",
                "date": sheet.date,
                "operation": child.operation,
                "total_pass_count": child.total_pass_count,
                "earning": child.amount,
                "rate": child.rate
            }
            unified_map[key]["rows"].append(row)
            unified_map[key]["total_pass_count"] += child.total_pass_count or 0
            unified_map[key]["total_earning"] += child.amount or 0
            unified_map[key]["total_rate"] += child.rate or 0

    # Prepare final data
    data_rows = []
    for key, emp in unified_map.items():
        data_rows.extend(emp["rows"])
        if group_by_employee:
            data_rows.append({
                "operator_id": f"<b>{emp['info']['operator_id']}</b>",
                "payroll_enrollment_id": f"<b>{emp['info']['payroll_enrollment_id']}</b>",
                "operator_name": f"<b>{emp['info']['operator_name']}</b>",
                "name": f"<b>{emp['info']['name']}</b>",
                "style_name": "<b>TOTAL</b>",
                "style_id": "-",
                "date": "-",
                "operation": "<b>TOTAL</b>",
                "total_pass_count": emp["total_pass_count"],
                "earning": emp["total_earning"],
                "rate": emp["total_rate"],
            })

    return columns, data_rows
