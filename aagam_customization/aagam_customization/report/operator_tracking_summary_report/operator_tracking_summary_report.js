// Copyright (c) 2025, Sushant and contributors
// For license information, please see license.txt

frappe.query_reports["Operator Tracking Summary Report"] = {
	"filters": [
		{
            fieldname: "fromdate",
            label: __("From Date"),
            fieldtype: "Date",
            // reqd: 1
        },
        {
            fieldname: "todate",
            label: __("To Date"),
            fieldtype: "Date",
            // reqd: 1
        },
        {
            fieldname: "group_by_employee",
            label: __("Group By Employee"),
            fieldtype: "Check"
        }

	]
};
