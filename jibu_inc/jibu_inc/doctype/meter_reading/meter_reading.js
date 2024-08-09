// Copyright (c) 2024, Chris and contributors
// For license information, please see license.txt

frappe.ui.form.on('Meter Reading', {
    closing_meter_reading: function(frm) {
        if (frm.doc.opening_meter_reading && frm.doc.closing_meter_reading) {
            frm.set_value("total", (parseFloat(frm.doc.closing_meter_reading) - parseFloat(frm.doc.opening_meter_reading)));
        }

    },
    opening_meter_reading: function(frm) {
        if (frm.doc.opening_meter_reading && frm.doc.closing_meter_reading) {
            frm.set_value("total", (parseFloat(frm.doc.closing_meter_reading) - parseFloat(frm.doc.opening_meter_reading)));
        }

    }
});