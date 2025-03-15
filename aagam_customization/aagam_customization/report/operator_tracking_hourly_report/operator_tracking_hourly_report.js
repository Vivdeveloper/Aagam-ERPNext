// Copyright (c) 2025, Sushant and contributors
// For license information, please see license.txt

frappe.query_reports["Operator Tracking Hourly Report"] = {
    filters: [
        {
            fieldname: "date",
            label: __("Date"),
            fieldtype: "Date",
            reqd: 1
        },
        {
            fieldname: "report_type",
            label: __("Report Type"),
            fieldtype: "Select",
            options: ["Operator Earning", "Bundle Hourly", "Style Track"],
            default: "Operator Earning",
            hidden: 1 // This will be controlled via the tabs
        }
    ],

    onload: function(report) {
        // Create custom tabs
        const tabs = ["Operator Earning", "Bundle Hourly", "Style Track"];
        
        let tabContainer = document.createElement("div");
        tabContainer.classList.add("custom-report-tabs");

        tabs.forEach(tab => {
            let tabBtn = document.createElement("button");
            tabBtn.innerText = tab;
            tabBtn.classList.add("btn", "btn-secondary", "report-tab-btn");
            tabBtn.dataset.reportType = tab;
            tabBtn.onclick = function() {
                frappe.query_report.set_filter_value("report_type", tab);
                frappe.query_report.refresh();
            };
            tabContainer.appendChild(tabBtn);
        });

        // Insert tabs into the report page
        setTimeout(() => {
            let reportArea = document.querySelector(".layout-main-section");
            if (reportArea && !document.querySelector(".custom-report-tabs")) {
                reportArea.prepend(tabContainer);
            }
        }, 500);
    }
};
