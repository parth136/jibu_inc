# Copyright (c) 2023, Chris and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PendingBottles(Document):
    @frappe.whitelist()
    def get_bottle_warehouse(self):
        warehouse = frappe.db.get_value("Bottles Warehouse Settings", {"company": self.company}, "default_warehouse")
        return warehouse

    def before_save(self):
        for d in self.get("items"):
            if not d.warehouse:
                d.warehouse = self.get_bottle_warehouse()

    def before_submit(self):
        for d in self.get("items"):
            if not d.warehouse:
                d.warehouse = self.get_bottle_warehouse()

            if d.pending_action == "Return of Pending Bottle":
                create_material_receipt(self.customer, self.name, d.item_code, d.qty, d.warehouse)
                update_customer(self.customer, d.qty, d.pending_action)
            elif d.pending_action == "Record Pending Bottle":
                create_material_issue(self.customer, self.name, d.item_code, d.qty, d.warehouse)
                update_customer(self.customer, d.qty, d.pending_action)


def create_material_receipt(customer,pending_bottle_ref, item_code, qty, warehouse):
    doc = frappe.get_doc({
        'doctype': 'Stock Entry',
        'stock_entry_type': 'Material Receipt',
        'pending_bottle_ref': pending_bottle_ref,
        'customer': customer,
        'items': [{
            'item_code': item_code,
            'qty': qty,
            't_warehouse': warehouse
        }]
    })
    # save and submit the document
    doc.insert()
    doc.submit()

def create_material_issue(customer,pending_bottle_ref,item_code, qty, warehouse):
    # create a new Stock Entry document
    doc = frappe.get_doc({
        'doctype': 'Stock Entry',
        'stock_entry_type': 'Material Issue',
        'pending_bottle_ref': pending_bottle_ref,
        'customer': customer,
        'items': [{
            'item_code': item_code,
            'qty': qty,
            's_warehouse': warehouse
        }]
    })
    # save and submit the document
    doc.insert()
    doc.submit()


def update_customer(customer, qty, p_type):
    pending_b_count = int(frappe.db.get_value("Customer", customer, "pending_bottles_count"))
    if pending_b_count is None:
        pending_b_count = 0
    if qty > 0 and p_type == "Record Pending Bottle":
        pending_bottles = "Yes"
        pending_b_count += int(qty)

    if qty > 0 and p_type == "Return of Pending Bottle":
        pending_b_count -= int(qty)
        if pending_b_count <= 0:
            pending_bottles = "No"
        else:
            pending_bottles = "Yes"

    frappe.db.set_value("Customer", customer, {
        'pending_bottles_count': pending_b_count,
        'pending_bottles': pending_bottles
    },update_modified=False)
