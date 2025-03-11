frappe.listview_settings['Timesheet'] = {
    onload: function(listview) {
        frappe.after_ajax(() => {  // Ensures button loads after all resources
            if (listview.page && listview.page.add_inner_button) {
                listview.page.add_inner_button(__('Fetch Data'), function() {
                    let d = new frappe.ui.Dialog({
                        title: 'Fetch Timesheet Data',
                        fields: [
                            {
                                label: 'From Date',
                                fieldname: 'from_date',
                                fieldtype: 'Date',
                                reqd: 1
                            },
                            {
                                label: 'To Date',
                                fieldname: 'to_date',
                                fieldtype: 'Date',
                                reqd: 1
                            }
                        ],
                        primary_action_label: 'Fetch',
                        primary_action(values) {
                            frappe.call({
                                method: 'aagam_customization.aagam_customization.doctype.custom_script.fetch_timesheet.fetch_timesheets',
                                args: {
                                    from_date: values.from_date,
                                    to_date: values.to_date
                                },
                                callback: function(response) {
                                    if (response.message) {
                                        frappe.msgprint(__('Timesheets created successfully'));
                                        listview.refresh();
                                    }
                                }
                            });
                            d.hide();
                        }
                    });
                    d.show();
                });
            } else {
                console.log("ListView not fully loaded yet.");
            }
        });
    }
};
