import frappe
import requests
from frappe.utils import getdate, nowdate
from datetime import datetime, timedelta

# API Constants
STITCH_BASE_URL = "http://portal2.stitcherp.com"
STITCH_API_SECRET_KEY = "674eea38-f7a7-45d5-8317-d6295287b125"

@frappe.whitelist()
def fetch_timesheets(from_date, to_date):
    """
    Fetch timesheet data from the external API and create timesheets in ERPNext.
    Ensures that no duplicate timesheets are created for the same operator on the same date.
    """
    # print("############")
    from_date = getdate(from_date)
    to_date = getdate(to_date)

    # API URL
    url = f"{STITCH_BASE_URL}/api/integration/operator-tracking-hourly-report"

    # Headers
    headers = {
        "STITCH-KEY": STITCH_API_SECRET_KEY,
        "Content-Type": "application/json"
    }

    # Generate date range manually (Frappe's date_range is not available)
    date_range = [(from_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((to_date - from_date).days + 1)]
    # print(date_range)
    for formatted_date in date_range:
        params = {"date": formatted_date}

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()  # Raise an error for HTTP failures (4xx, 5xx)
            data = response.json()

            # Debugging: Log API Response
            # frappe.log_error(f"API Response for {formatted_date}: {data}", "Timesheet API Debug")
            process_timesheet_data(data["data"], formatted_date)
            # if data.get("status") == "success" and data.get("data"):
            #     print("######################################")
                # process_timesheet_data(data["data"], formatted_date)
            # else:
            #     frappe.log_error(f"No valid data found for {formatted_date}", "Timesheet API")

        except requests.exceptions.RequestException as e:
            frappe.log_error(f"Error fetching data for {formatted_date}: {str(e)}", "Timesheet API")


def process_timesheet_data(data, date):
    # print("Processing Timesheet Data...")  # Debug
    for operator_id, operator_data in data.items():
        # print(f"Operator ID: {operator_id}, Data: {operator_data}")  # Debug

        if not operator_data:
            continue

        operator_name = operator_data.get("name")
        payroll_enrollment_id = operator_data.get("payroll_enrollment_id")

        # Check for existing timesheets
        existing_timesheet = frappe.db.exists(
            "Timesheet",
            {"custom_operator_id_": operator_id, "start_date": date}
        )

        if existing_timesheet:
            print(f"Skipping duplicate timesheet for {operator_name} on {date}")  # Debug
            continue

        timesheet = frappe.new_doc("Timesheet")
        timesheet.company = "SHREE VARDHMAN IMPEX"
        timesheet.employee = payroll_enrollment_id
        timesheet.employee_name = operator_name
        timesheet.custom_operator_id_ = operator_id
        timesheet.custom_operator_name = operator_name
        timesheet.custom_payroll_id = payroll_enrollment_id
        timesheet.start_date = date
        timesheet.end_date = date
        timesheet.total_hours = 0
        timesheet.custom_earnings = 0

        total_hours = 0
        total_earnings = 0

        for style in operator_data.get("styles", []):
            # print(f"Processing Style: {style}")  # Debug
            style_name = style.get("style_name")
            style_id = style.get("style_id")

            for style_data in style.get("style_data", []):
                # print(f"Processing Style Data: {style_data}")  # Debug

                # Validate and convert date format
                style_data_date = style_data.get("date")
                if isinstance(style_data_date, str):
                    try:
                        style_data_date = datetime.strptime(style_data_date, "%d-%m-%Y").strftime("%Y-%m-%d")
                    except ValueError:
                        frappe.log_error(f"Invalid date format: {style_data_date}", "Timesheet API")
                        continue

                if style_data_date != date:
                    print(f"Skipping style data: {style_data_date} != {date}")  # Debug
                    continue

                # Extract fields
                operation = style_data.get("operation")
                total_pass_count = style_data.get("total_pass_count", 0)
                earning = style_data.get("earning", 0)
                rate = style_data.get("rate", 0)
                shift_hour_count = style_data.get("shift_hour_count", 0)

                print(f"Adding Log: {shift_hour_count} hrs, {style_name}, {operation}, {earning}")  # Debug

                total_hours += shift_hour_count
                total_earnings += earning
                # ttl += total_pass_count
                billing_rate = style_data.get("rate", 0)
                billing_amount = billing_rate * style_data.get("total_pass_count", 0) 
                # from_time = datetime.strptime(date, "%Y-%m-%d")
                # to_time = from_time + timedelta(hours=shift_hour_count)

                timesheet.append("time_logs", {
                    "activity_type": "Earnings",
                    # "from_time": from_time.strftime("%Y-%m-%d %H:%M:%S"),
                    # "to_time": to_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "hours": billing_rate,
                    "custom_style_id": style_id,
                    "custom_style_name": style_name,
                    "custom_operation": operation,
                    # "from_time": date,
                    # "to_time": date,
                    "custom_total_pass_count": total_pass_count,
                    "is_billable": 1,
                    # "billing_amount": earning,
                    "billing_rate": billing_rate,
                    "billing_amount": billing_amount,
                    "costing_rate" : billing_rate,
                    "costing_amount":billing_amount,
                    "billing_hours": total_pass_count
                })

        # timesheet.total_hours = total_hours
        timesheet.custom_earnings = total_earnings
        
        # timesheet.total_billed_hours = ttl
        # Save and submit the timesheet
        timesheet.insert(ignore_permissions=True)
        # timesheet.total_costing_amount = timesheet.total_billable_amount
        # timesheet.submit()

        print(f"Timesheet Created: {operator_name} on {date}")  # Debug
