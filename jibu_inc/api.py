import frappe
from frappe.utils import get_datetime


@frappe.whitelist()
def create_customer(customer_name, customer_group, type_of_customer, email_id=None, mobile_no=None, posa_referral_company=None, gps_location=None, location_photo=None, address_description=None):
    if posa_referral_company is None:
        company = frappe.get_default_company()
    else:
        company = posa_referral_company

    default_currency = frappe.db.get_value('Company', company, 'default_currency')
    territory_name = frappe.db.get_value('Company', company, 'country')
    territory_exists = frappe.db.exists('Territory', territory_name)

    if not territory_exists:
        new_territory = frappe.get_doc({
            'doctype': 'Territory',
            'territory_name': territory_name,
            'is_group': 0,
            'parent_territory': 'All Territories'
        })
        new_territory.flags.ignore_permissions = True
        new_territory.save()

    customer = frappe.get_doc({
        'doctype': 'Customer',
        'customer_name': customer_name,
        'customer_type': 'Individual' if type_of_customer == 'Households' else 'Company',
        'territory': territory_name,
        'customer_group': customer_group,
        'type_of_customer': type_of_customer,
        'posa_referral_company': posa_referral_company,
        'email_id': email_id,
        'mobile_no': mobile_no,
        'gps_location': gps_location,
        'location_photo': location_photo,
        'address_description': address_description,
        'default_price_list': frappe.db.get_value('Customer Group', customer_group, 'default_price_list'),
        'default_currency': default_currency
    })

    customer.insert(ignore_permissions=True)
    return customer.name


@frappe.whitelist()
def check_payments(contact_mobile):
    payment_entry = frappe.get_list('Mpesa Payment Entry',
                                    filters={
                                        'msisdn': contact_mobile,
                                        'submit_payment': ['!=', 1]
                                    },
                                    fields=["transamount", "transid", "full_name","mode_of_payment","name"],
                                    limit_page_length=1)

    if payment_entry:
        return payment_entry[0]
    else:
        return None


@frappe.whitelist()
def update_pending_bottles(customers, posa_referral_company, pending_action, qty,bottle_type, pos_profile, owner=None, warehouse=None):
    # Get the customer associated with the POS Invoice
    customer = frappe.get_doc("Customer", customers)
    pos = frappe.get_doc("POS Profile", pos_profile)
    if warehouse and warehouse != "":
        set_warehouse = warehouse
    else:
        set_warehouse = pos.warehouse
    pending_b_count = int(customer.pending_bottles_count)
    if pending_b_count is None:
        pending_b_count = 0
    # Update the customer fields
    if pending_action == "Return of Pending Bottle":

        # pending_b_count += int(doc.pending_bottle)
        po = pending_b_count - int(qty)
        customer.pending_bottles_count = po
        if po > 0:
            customer.pending_bottles = "Yes"
        else:
            customer.pending_bottles = "No"


        docs = frappe.get_doc({
            'doctype': 'Pending Bottles',
            'customer': customers,
            'posted_by': owner if owner else "",
            'company': posa_referral_company,
            'items': [{
                'bottle_type': bottle_type,
                'pending_action': pending_action,
                'qty': int(qty),
                'warehouse': set_warehouse,
                'customer': customers,
            }]
        })
        docs.insert(ignore_permissions=True)
        docs.submit()

    if pending_action == "Record Pending Bottle":
        po_bottles = int(qty) + pending_b_count
        customer.pending_bottles_count = po_bottles
        if po_bottles > 0:
            customer.pending_bottles = "Yes"
        else:
            customer.pending_bottles = "No"
        docs = frappe.get_doc({
            'doctype': 'Pending Bottles',
            'customer': customers,
            'posted_by': owner if owner else "",
            'company': posa_referral_company,
            'items': [{
                'bottle_type': bottle_type,
                'pending_action': pending_action,
                'qty': int(qty),
                'warehouse': set_warehouse,
                'customer': customers,
            }]
        })
        docs.insert(ignore_permissions=True)
        docs.submit()
    customer.save(ignore_permissions=True)


@frappe.whitelist()
def get_pos_invoice_items(start, end, pos_profile, user):
    data = frappe.db.sql(
        """
        select
            pii.item_code,
            sum(pii.qty) as "cumulative_qty",
            sum(pii.base_amount) as "total_base_amount",
            sum(pii.base_net_amount) as "total_base_net_amount"
        from
            `tabPOS Invoice` as pi join `tabPOS Invoice Item` as pii on pi.name = pii.parent
        where
            pi.owner = %s and pi.docstatus = 1 and pi.pos_profile = %s and ifnull(pi.consolidated_invoice,'') = ''
        group by
            pii.item_code
        """,
        (user, pos_profile),
        as_dict=1,
    )
    return data
