// Copyright (c) 2025, Sushant and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Costing", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on('Costing', {
    fabric_cost: function(frm) {
        calculate_ttl(frm);
    },
    fabric_construction: function(frm) {
        calculate_ttl(frm);
    },
    testing: function(frm) {
        calculate_total(frm);
    },
    cut_make_trim: function(frm) {
        calculate_total(frm);
    },
    accessory: function(frm) {
        calculate_total(frm);
    },
    label_tag: function(frm) {
        calculate_total(frm);
    },
    packing: function(frm) {
        calculate_total(frm);
    },
    logistic: function(frm) {
        calculate_total(frm);
    },
    overhead_3value: function(frm) {
        calculate_cost(frm);
    },
    cost: function(frm) {
        calculate_margin(frm);
    },
    refresh: function(frm) {
        calculate_ttl(frm);
        calculate_total(frm);
        calculate_cost(frm);
        calculate_margin(frm);
    }
});

function calculate_ttl(frm) {
    let fabric_cost = frm.doc.fabric_cost || 0;
    let fabric_construction = frm.doc.fabric_construction || 0;
    frm.set_value('ttl', fabric_cost * fabric_construction);
}

function calculate_total(frm) {
    let testing = frm.doc.testing || 0;
    let cut_make_trim = frm.doc.cut_make_trim || 0;
    let accessory = frm.doc.accessory || 0;
    let label_tag = frm.doc.label_tag || 0;
    let packing = frm.doc.packing || 0;
    let logistic = frm.doc.logistic || 0;
    let total = testing + cut_make_trim + accessory + label_tag + packing + logistic;
    frm.set_value('total', total);
    calculate_cost(frm);
}

function calculate_cost(frm) {
    let total = frm.doc.total || 0;
    let overhead_3value = frm.doc.overhead_3value || 0;
    let cost = total + overhead_3value;
    frm.set_value('cost', cost);
    calculate_margin(frm);
}

function calculate_margin(frm) {
    let cost = frm.doc.cost || 0;
    let margin_12 = cost * 0.12;
    frm.set_value('12_margin', margin_12);
    frm.set_value('final_cost', cost + margin_12);
}

