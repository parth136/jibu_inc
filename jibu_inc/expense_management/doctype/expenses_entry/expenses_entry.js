// Copyright (c) 2023, Pointershub Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Expenses Entry', {
	// refresh: function(frm) {

	// }
    onload: function (frm){
        frm.set_query('mode_of_payment', {filters: {type: ['in', ['Cash', 'Bank', 'Phone']]}});
        frm.set_query( "party_type",'expenses', {filters: {name: ['in', ['Employee', 'Supplier']]}});
        frm.set_query('default_cost_center', { filters: { company: frm.doc.company, is_group: 0} });
        frm.set_query('cost_center',"expenses", { filters: { company: frm.doc.company, is_group: 0} });

    },

    mode_of_payment: function(frm) {
        if (frm.doc.mode_of_payment && frm.doc.company) {
            frm.call({
                method: "get_mode_of_payment_details",
                doc: frm.doc,
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('liability_or_asset_account', r.message.payment_account);
                        frm.set_value('payment_currency', r.message.payment_currency);
                    }
                }
            });
        }
    },
    company: function(frm) {
        frm.set_query('liability_or_asset_account', {
            filters: {
                root_type: ['in', ['Liability', 'Asset']],
                company: frm.doc.company
            }
        });

        frm.set_query('default_cost_center', {
            filters: {
                company: frm.doc.company,
                is_group: 0
            }
        });

        frm.fields_dict['expenses'].grid.get_field('account').get_query = function(doc, cdt, cdn) {
            return {
                filters: {
                    root_type: 'Expense',
                    company: frm.doc.company,
                    is_group: 0
                }
            };
        };

        frm.fields_dict['expenses'].grid.get_field('cost_center').get_query = function(doc, cdt, cdn) {
            return {
                filters: {
                    company: frm.doc.company,
                    is_group: 0
                }
            };
        };

        frm.refresh_field('expenses');

    },
    expenses_remove: function(frm, cdt, cdn) {
        calculate_total(frm);
    }
});

frappe.ui.form.on('Expenses Item', {
    rate: function(frm, cdt, cdn) {
        var d = locals[cdt][cdn];
        if (d.rate && d.qty) {
            frappe.model.set_value(cdt, cdn, 'amount', flt(d.rate * d.qty));
            calculate_total(frm);
        }
    },
    qty: function(frm, cdt, cdn) {
        var d = locals[cdt][cdn];
        if (d.rate && d.qty) {
            frappe.model.set_value(cdt, cdn, 'amount', flt(d.rate * d.qty));
            calculate_total(frm);
        }
    }
});

function calculate_total(frm) {
    let total = 0;
    $.each(frm.doc.expenses || [], function(i, d) {
        total += flt(d.amount);
    });
    frm.set_value('total', total);
    refresh_field('total');
}