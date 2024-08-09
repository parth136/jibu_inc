function set_prods_data(data, frm) {
	data.forEach(d => {
		add_to_pos_products(d, frm);
	});
	frm.refresh_field("pos_products");
}

function add_to_pos_products(d, frm) {
	frm.add_child("pos_products", {
		item_code: d.item_code,
		cumulative_qty: d.cumulative_qty,
		total_base_amount: d.total_base_amount,
		total_base_net_amount: d.total_base_net_amount
	})
}

frappe.ui.form.on('POS Closing Entry', {
	pos_opening_entry(frm) {
		if (frm.doc.pos_opening_entry && frm.doc.period_start_date && frm.doc.period_end_date && frm.doc.user) {
			frappe.run_serially([
				() => frm.trigger("get_pos_invoice_items")
			]);
		}
	},
	get_pos_invoice_items(frm) {
		return frappe.call({
			method: 'jibu_inc.api.get_pos_invoice_items',
			args: {
				start: frappe.datetime.get_datetime_as_string(frm.doc.period_start_date),
				end: frappe.datetime.get_datetime_as_string(frm.doc.period_end_date),
				pos_profile: frm.doc.pos_profile,
				user: frm.doc.user
			},
			callback: (r) => {
				let pos_p = r.message;
				set_prods_data(pos_p, frm);
				console.log(r)
			}
		});
	},

})