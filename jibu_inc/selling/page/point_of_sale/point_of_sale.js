frappe.provide('erpnext.PointOfSale');

frappe.pages['point-of-sale'].on_page_load = function(wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Point of Sales'),
		single_column: true
	});

	frappe.require('assets/js/point-of-sale.min.js', function() {
		wrapper.pos = new erpnext.PointOfSale.Controller(wrapper);
		window.cur_pos = wrapper.pos;
	});

	wrapper.pos.page.add_inner_button(__("Add Customer"), () => {
            add_customer_dialog(wrapper.pos);
        });

};

frappe.pages['point-of-sale'].refresh = function(wrapper) {
	if (document.scannerDetectionData) {
		onScan.detachFrom(document);
		wrapper.pos.wrapper.html("");
		wrapper.pos.check_opening_entry();
	}
};

function add_customer_dialog(pos_instance) {
    let dialog = new frappe.ui.Dialog({
        title: __("Add Customer"),
        fields: [
            { fieldname: 'customer_name', fieldtype: 'Data', label: __("Customer Name"), reqd: 1 },
            { fieldname: 'email_id', fieldtype: 'Data', label: __("Email ID") },
            { fieldname: 'mobile_no', fieldtype: 'Data', label: __("Mobile No") },
        ],
        primary_action_label: __("Save"),
        primary_action: (values) => {
            frappe.call({
                method: 'jibu_inc.jibu_inc.api.create_customer',
                args: {
                    customer_name: values.customer_name,
                    email_id: values.email_id,
                    mobile_no: values.mobile_no,
                },
                callback: (r) => {
                    if (!r.exc) {
                        pos_instance.customer_field.set_value(r.message);
                        dialog.hide();
                    }
                },
            });
        },
    });
    dialog.show();
}