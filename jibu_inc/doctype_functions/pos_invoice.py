from __future__ import unicode_literals
import frappe
import erpnext
from frappe import _, throw


def purchase_count_fn(doc, method):
	# Get the initial purchase count from the customer
	count = frappe.db.get_value("Customer", doc.customer, "purchase_count") or 0

	# Accumulator for the count during the iteration
	total_new_or_refill_qty = 0

	# Iterate through items and accumulate the quantity of relevant items
	for item in doc.items:
		if 'NEW' in item.item_code.upper() or 'REFILL' in item.item_code.upper():
			# your code here
			# if 'NEW' in item.item_code or 'Refill' in item.item_code:
			total_new_or_refill_qty += item.qty

	# Update the purchase count only if there's an increase in quantity
	if total_new_or_refill_qty > 0:
		updated_count = int(count) + int(total_new_or_refill_qty)
		frappe.db.set_value("Customer", doc.customer, "purchase_count", updated_count)
