// Copyright (c) 2025, Sushant and contributors
// For license information, please see license.txt

frappe.query_reports["Operator Tracking Hourly Report"] = {
	"filters": [
		{
			"fieldname": "date",
			"label": "Date",
			"fieldtype": "Date",
			"default": "Today"
		}
	]
	
};
