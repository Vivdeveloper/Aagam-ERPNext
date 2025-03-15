import requests
import frappe

# API Configuration
STITCH_BASE_URL = "http://portal2.stitcherp.com"
STITCH_API_SECRET_KEY = "674eea38-f7a7-45d5-8317-d6295287b125"

def execute(filters=None):
    if not filters or not filters.get("date"):
        frappe.throw("Date filter is required")

    if not filters.get("report_type"):
        frappe.throw("Report Type filter is required")

    date = filters.get("date")
    report_type = filters.get("report_type")

    # API URL
    url = f"{STITCH_BASE_URL}/api/integration/operator-tracking-hourly-report"

    # Headers
    headers = {
        "STITCH-KEY": STITCH_API_SECRET_KEY,
        "Content-Type": "application/json"
    }

    # Query Parameters
    params = {"date": date}

    # Fetch API Data
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        frappe.throw(f"API Request Failed: {str(e)}")

    # Parse JSON response
    data = response.json()

    if data.get("status") != "success":
        frappe.throw(data.get("data", {}).get("message", "Unknown error"))

    # Extracting operator data
    operators = data.get("data", {})

    # Define columns based on the selected report type
    report_columns = {
        "Operator Earning": [
            {"fieldname": "payroll_enrollment_id", "label": "Payroll ID", "fieldtype": "Data", "width": 120},
            {"fieldname": "operator_name", "label": "Operator Name", "fieldtype": "Data", "width": 150},
            {"fieldname": "name", "label": "Name", "fieldtype": "Data", "width": 150},
            {"fieldname": "line", "label": "Line", "fieldtype": "Data", "width": 100},
            {"fieldname": "style_name", "label": "Style Name", "fieldtype": "Data", "width": 150},
            {"fieldname": "operation", "label": "Operation", "fieldtype": "Data", "width": 150},
            {"fieldname": "total_pass_count", "label": "Total Pass Count", "fieldtype": "Int", "width": 120},
            {"fieldname": "earning", "label": "Earning", "fieldtype": "Currency", "width": 120},
            {"fieldname": "efficiency", "label": "Efficiency", "fieldtype": "Float", "width": 120}
        ],
        "Bundle Hourly": [
            {"fieldname": "payroll_enrollment_id", "label": "Payroll ID", "fieldtype": "Data", "width": 120},
            {"fieldname": "operator_name", "label": "Operator Name", "fieldtype": "Data", "width": 150},
            {"fieldname": "line", "label": "Line", "fieldtype": "Data", "width": 100},
            {"fieldname": "hour_1", "label": "Hour 1", "fieldtype": "Int", "width": 100},
            {"fieldname": "hour_2", "label": "Hour 2", "fieldtype": "Int", "width": 100},
            {"fieldname": "hour_3", "label": "Hour 3", "fieldtype": "Int", "width": 100},
            {"fieldname": "hour_4", "label": "Hour 4", "fieldtype": "Int", "width": 100},
            {"fieldname": "hour_5", "label": "Hour 5", "fieldtype": "Int", "width": 100},
            {"fieldname": "hour_6", "label": "Hour 6", "fieldtype": "Int", "width": 100},
            {"fieldname": "hour_7", "label": "Hour 7", "fieldtype": "Int", "width": 100},
            {"fieldname": "hour_8", "label": "Hour 8", "fieldtype": "Int", "width": 100},
            {"fieldname": "total_pass_count", "label": "Total Production", "fieldtype": "Int", "width": 120},
            {"fieldname": "efficiency", "label": "Efficiency", "fieldtype": "Float", "width": 120}
        ],
        "Style Track": [
            {"fieldname": "operator_name", "label": "Operator Name", "fieldtype": "Data", "width": 150},
            {"fieldname": "style_name", "label": "Style Name", "fieldtype": "Data", "width": 150},
            {"fieldname": "line", "label": "Line", "fieldtype": "Data", "width": 100},
            {"fieldname": "total_pass_count", "label": "Total Pass Count", "fieldtype": "Int", "width": 120},
            {"fieldname": "operation", "label": "Operation", "fieldtype": "Data", "width": 150},
        ]
    }

    # Determine the selected columns
    columns = report_columns.get(report_type, [])

    data_rows = []

    for operator_id, operator_info in operators.items():
        for style in operator_info.get("styles", []):
            for style_data in style.get("style_data", []):
                row = {
                    "payroll_enrollment_id": operator_info.get("payroll_enrollment_id"),
                    "operator_name": operator_info.get("operator_name"),
                    "name": operator_info.get("name"),
                    "line": operator_info.get("line"),
                    "style_name": style.get("style_name"),
                    "operation": style_data.get("operation"),
                    "total_pass_count": style_data.get("total_pass_count"),
                    "earning": style_data.get("earning"),
                    "efficiency": style_data.get("efficiency"),
                    "hour_1": style_data.get("HOUR 1"),
                    "hour_2": style_data.get("HOUR 2"),
                    "hour_3": style_data.get("HOUR 3"),
                    "hour_4": style_data.get("HOUR 4"),
                    "hour_5": style_data.get("HOUR 5"),
                    "hour_6": style_data.get("HOUR 6"),
                    "hour_7": style_data.get("HOUR 7"),
                    "hour_8": style_data.get("HOUR 8"),
                }

                # Filter out unnecessary columns based on report type
                filtered_row = {key: value for key, value in row.items() if key in [col["fieldname"] for col in columns]}
                data_rows.append(filtered_row)

    return columns, data_rows
