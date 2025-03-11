import requests
import frappe

# API Configuration
STITCH_BASE_URL = "http://portal2.stitcherp.com"
STITCH_API_SECRET_KEY = "674eea38-f7a7-45d5-8317-d6295287b125"

def execute(filters=None):
    if not filters or not filters.get("date"):
        frappe.throw("Date filter is required")
    
    date = filters.get("date")  # Get the date from filters
    
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
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        frappe.throw(f"API Request Failed: {str(e)}")
    
    # Parse JSON response
    data = response.json()

    if data.get("status") != "success":
        frappe.throw(data.get("data", {}).get("message", "Unknown error"))

    # Extracting operator data
    operators = data.get("data", {})

    # Dynamically determine all possible fields
    all_fieldnames = set([
        "operator", "operator_name", "name", "payroll_enrollment_id",
        "style_name", "style_id", "date", "operation_id", "operation_name"
    ])
    
    data_rows = []
    
    for operator_id, operator_info in operators.items():
        for style in operator_info.get("styles", []):
            for style_data in style.get("style_data", []):
                row = {
                    "operator": operator_info.get("operator"),
                    "operator_name": operator_info.get("operator_name"),
                    "name": operator_info.get("name"),
                    "payroll_enrollment_id": operator_info.get("payroll_enrollment_id"),
                    "style_name": style.get("style_name"),
                    "style_id": style.get("style_id"),
                    "date": style_data.get("date"),
                    "operation_id": style_data.get("operation_id"),
                    "operation_name": style_data.get("operation_name"),
                }
                
                # Capture all additional dynamic fields (HOUR-5, sam, rate, efficiency, etc.)
                for key, value in style_data.items():
                    if key not in row:
                        row[key] = value
                        all_fieldnames.add(key)
                
                data_rows.append(row)
    
    # Generate dynamic columns based on all field names
    columns = [{"fieldname": field, "label": field.replace("_", " ").title(), "fieldtype": "Data", "width": 120} for field in all_fieldnames]

    return columns, data_rows
