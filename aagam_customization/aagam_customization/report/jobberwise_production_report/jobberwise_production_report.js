// Copyright (c) 2025, Sushant and contributors
// For license information, please see license.txt

frappe.query_reports["Jobberwise Production Report"] = {
	"filters": [
		{
            "fieldname": "from_date",
            "label": "From Date",
            "fieldtype": "Date",
            "reqd": 1,
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
        },
        {
            "fieldname": "to_date",
            "label": "To Date",
            "fieldtype": "Date",
            "reqd": 1,
            "default": frappe.datetime.get_today()
        },
        {
            "fieldname": "employee",
            "label": "Employee",
            "fieldtype": "Link",
            "options": "Employee"
        },
        {
            "fieldname": "department",
            "label": "Department",
            "fieldtype": "Link",
            "options": "Department"
        },
        {
            "fieldname": "production_plan",
            "label": "Production Plan",
            "fieldtype": "Link",
            "options": "Production Plan"
        },
        {
            "fieldname": "operation",
            "label": "Operation",
            "fieldtype": "Link",
            "options": "Operation"
        },
        {
            "fieldname": "grp_by_emp",
            "label": "Group by Employee",
            "fieldtype": "Check"
        }

	]
};
