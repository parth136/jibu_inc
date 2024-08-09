frappe.ui.form.on('POS Invoice', {
    onload: function (frm) {
        if (frappe.pages['point-of-sale'] && frappe.pages['point-of-sale'].pos) {
            add_customer_button(frm, frappe.pages['point-of-sale'].pos);
        }
    },
    check_payments: function(frm){
       check_payments_final(frm);
    }
});

function add_customer_button(frm, pos_instance) {
    pos_instance.page.add_inner_button(__("Add Customer"), () => {
        add_customer_dialog(frm, pos_instance);
    });

    // pos_instance.page.add_inner_button(__("Pending Bottles"), () => {
    //     add_pending_bottle_dialog(frm, pos_instance);
    // });
}

function add_customer_dialog(frm, pos_instance) {
    let dialog = new frappe.ui.Dialog({
        title: __("Add Customer"),
        fields: [
            { fieldname: 'customer_name', fieldtype: 'Data', label: __("Customer Name"), reqd: 1 },
            { fieldname: 'customer_group', fieldtype: 'Link', options: 'Customer Group', label: __('Customer Group'), column: 2, reqd: 1 },
            { fieldname: 'type_of_customer', fieldtype: 'Select', label: __('Type of Customer'), options: 'Businesses / Offices\nHouseholds\nResellers', reqd: 1, column: 1 },
            { fieldname: 'mobile_no', fieldtype: 'Data', label: __("Mobile No"), reqd: 1},
            { fieldname: 'secondary_mobile_no', fieldtype: 'Data', label: __("Alternative Mobile No") },
            { fieldname: 'address_description', fieldtype: 'Data', label: __("Address Description") },
            { fieldname: 'gps_location', fieldtype: 'Geolocation', label: __("GPS location") },
            { fieldname: 'location_photo', fieldtype: 'Attach Image', label: __("Location Photo") },
        ],
        primary_action_label: __("Save"),
        primary_action: (values) => {
            // Here is where we add the save button disabling logic
            let saveButton = $(".modal-footer .btn-primary:visible");
            saveButton.attr("disabled", true);

            frappe.call({
                method: 'jibu_inc.api.create_customer',
                args: {
                    customer_name: values.customer_name,
                    customer_group: values.customer_group,
                    email_id: values.email_id,
                    mobile_no: values.mobile_no,
                    type_of_customer: values.type_of_customer,
                    posa_referral_company: frm.doc.company,
                    gps_location: values.gps_location,
                    location_photo: values.location_photo,
                    address_description: values.address_description,
                },
                callback: (r) => {
                    if (!r.exc) {
                        console.log(pos_instance)
                        pos_instance.frm.doc.customer = r.message;
                        $('.customer-search-field').val(r.message).trigger('input');
                        // Set the new customer's name in the customer search field using jQuery
                        $('input.input-with-feedback.form-control[data-target="Customer"]').val(r.message);

                        // Trigger the input event to update the customer field in the POS
                        $('input.input-with-feedback.form-control[data-target="Customer"]').trigger('input');
                        dialog.hide();
                        frm.set_value("customer", r.message)

                        // Refresh the form to see the changes
                        pos_instance.frm.refresh_field('customer');
                        frm.refresh_field('customer');

                    } else {
                        saveButton.attr("disabled", false);
                    }
                },
            });
        },
    });
    dialog.show();
}



function add_pending_bottle_dialog(frm, pos_instance) {
    let dialog = new frappe.ui.Dialog({
        title: __("Pending Bottle"),
        fields: [
            { fieldname: 'customer', fieldtype: 'Link', options: 'Customer', label: __('Customer'), column: 2, reqd: 1 },
//            { fieldname: 'posa_referral_company', fieldtype: 'Link', options: 'Company', label: __('Franchise'), column: 2, default: frm.doc.company, reqd: 1 },
            { fieldname: 'pending_action', fieldtype: 'Select', label: __("Action"), options: '\nRecord Pending Bottle\nReturn of Pending Bottle', reqd: 1 },
            { fieldname: 'bottle_type', fieldtype: 'Select', label: __("Bottle"), options: '\n10 Litre \n20 Litre \n 18.9 Litre', reqd: 1 },
//            { fieldname: 'bottle_type', fieldtype: 'Link', options: 'Item', label: __('Bottle'), column: 2, reqd: 1 },
            { fieldname: 'qty', fieldtype: 'Int', label: __("Qty"), default: 1, reqd: 1},
        ],
        primary_action_label: __("Save"),
        primary_action: (values) => {
            // Disable the primary action button
            dialog.get_primary_btn().attr('disabled', true);

            frappe.call({
                method: 'jibu_inc.api.update_pending_bottles',
                args: {
                    customers: values.customer,
                    posa_referral_company: pos_instance.frm.doc.company,
                    pending_action: values.pending_action,
                    qty: values.qty,
                    bottle_type: values.bottle_type,
                    pos_profile: pos_instance.frm.doc.pos_profile,
                    owner: pos_instance.frm.doc.owner,
                    warehouse: pos_instance.frm.doc.set_warehouse
                },
                callback: (r) => {
                    console.log(r)
                    if (!r.exc) {
                        dialog.hide();
                        frappe.show_alert({message:__('We\'ve entered the details successfully!'), indicator:'green'}, 5);
                    }
                    // Enable the primary action button again
                    dialog.get_primary_btn().attr('disabled', false);
                },
                always: () => {
                    // Enable the primary action button regardless of outcome
                    dialog.get_primary_btn().attr('disabled', false);
                }
            });
        },
    });
    dialog.show();
}


function check_payments(frm) {
    let contact_mobile = frm.doc.contact_mobile;
    if (contact_mobile) {
        frappe.call({
            method: 'jibu_inc.api.check_payments',
            args: {
                contact_mobile: contact_mobile
            },
            callback: function(r) {
                // If there is a match, then display a popup with the details
                if (r.message) {
                    let full_name = r.message.full_name;
                    let transamount = r.message.transamount;
                    let transid = r.message.transid;
                    let mode_of_payment = r.message.mode_of_payment;  // Get the mode of payment from the API response
                    frappe.confirm(
                        `Mobile: ${contact_mobile}<br>Receipt: ${transid}<br>Name: ${full_name}<br>Amount: ${transamount}<br>Payment Mode: ${mode_of_payment}<br><br>Do you want to populate these details?`,
                        function() {
                            // If "Yes" is clicked, populate the fields
                            frm.set_value('paid_amount', transamount);
                            frm.set_value('mpesa_receipt_number', transid);
                            frm.refresh_field('paid_amount');
                            frm.refresh_field('mpesa_receipt_number');

                            // Find the matching payment mode and set the amount to it
                            let matching_payment = frm.doc.payments.find(payment => payment.mode_of_payment === mode_of_payment);
                            if(matching_payment) {
                                matching_payment.amount = parseFloat(transamount);
                                frm.refresh_field('payments');
                            }
                        }
                    );
                }
            }
        });
    }
}


function set_mpesa_search_params(contact_mobile) {
    if (!contact_mobile) return;

    // Remove leading '+' if it exists and replace any leading '0' with '254'
    contact_mobile = contact_mobile.replace(/^\+/, '').replace(/^0/, '254');

    if(contact_mobile.length === 12){
        // Format the number as '2547 ***** 000'
        return contact_mobile.substring(0, 4) + ' ***** ' + contact_mobile.substring(9);
    } else {
        return undefined;
    }
}

function check_payments_final(frm) {
    let contact_mobile = frm.doc.contact_mobile;
    contact_mobile = set_mpesa_search_params(contact_mobile);

    if (contact_mobile) {
        frappe.call({
            method: 'jibu_inc.api.check_payments',
            args: {
                contact_mobile: contact_mobile
            },
            callback: function(r) {
                // If there is a match, then display a popup with the details
                if (r.message) {
                    let full_name = r.message.full_name;
                    let transamount = r.message.transamount;
                    let transid = r.message.transid;
                    let mode_of_payment = r.message.mode_of_payment;  // Get the mode of payment from the API response
                    frappe.confirm(
                        `Mobile: ${contact_mobile}<br>Receipt: ${transid}<br>Name: ${full_name}<br>Amount: ${transamount}<br>Payment Mode: ${mode_of_payment}<br><br>Do you want to populate these details?`,
                        function() {
                            // If "Yes" is clicked, populate the fields
                            frm.set_value('paid_amount', transamount);
                            frm.set_value('mpesa_receipt_number', transid);
                            frm.refresh_field('paid_amount');
                            frm.refresh_field('mpesa_receipt_number');

                            // Find the matching payment mode and set the amount to it
                            let matching_payment = frm.doc.payments.find(payment => payment.mode_of_payment === mode_of_payment);
                            if(matching_payment) {
                                matching_payment.amount = parseFloat(transamount);
                                frm.refresh_field('payments');
                            }
                        }
                    );
                }
            }
        });
    } else {
        frappe.msgprint('Invalid phone number. It should be 12 digits long starting with 254. or 07');
    }
}
