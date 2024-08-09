import frappe
import re
from frappe import _, throw
from frappe.utils import getdate


@frappe.whitelist()
def update_pos_products(doc, method):
	# Dictionary to store cumulative item data
	item_data = {}
	total_outstanding_amount = 0
	total_litres_sold_qty = 0

	# Iterate through each POS Transaction in the POS Closing Entry
	for transaction in doc.pos_transactions:
		pos_invoice_name = transaction.pos_invoice

		if not pos_invoice_name:
			continue

		pos_invoice = frappe.get_doc("POS Invoice", pos_invoice_name)

		if pos_invoice.outstanding_amount:
			total_outstanding_amount += pos_invoice.outstanding_amount

		# Fetch item details from POS Invoice Items
		invoice_items = frappe.get_all(
			"POS Invoice Item",
			filters={"parent": pos_invoice_name, "docstatus": 1},
			fields=["item_code", "qty", "base_amount", "base_net_amount"]
		)

		# Aggregate item details
		for item in invoice_items:
			if item.item_code not in item_data:
				item_data[item.item_code] = {
					"cumulative_qty": 0,
					"total_base_amount": 0,
					"total_base_net_amount": 0
				}

			# Use assignment instead of in-place addition
			item_data[item.item_code]["cumulative_qty"] = item_data[item.item_code]["cumulative_qty"] + item.qty
			item_data[item.item_code]["total_base_amount"] = item_data[item.item_code][
				                                                 "total_base_amount"] + item.base_amount
			item_data[item.item_code]["total_base_net_amount"] = item_data[item.item_code][
				                                                     "total_base_net_amount"] + item.base_net_amount

	# Clear existing items in the child table
	doc.set("pos_products", [])

	# Populate the child table with aggregated item data
	for item_code, data in item_data.items():
		total_litres = get_total_litres_sold(item_code, data["cumulative_qty"])
		total_litres_sold_qty += total_litres
		doc.append("pos_products", {
			"item_code": item_code,
			"cumulative_qty": data["cumulative_qty"],
			"total_base_amount": data["total_base_amount"],
			"total_base_net_amount": data["total_base_net_amount"],
			"total_litres": total_litres
		})

	doc.total_credit_amount = total_outstanding_amount
	doc.total_litres_sold_qty = total_litres_sold_qty

	calculate_total_litres_and_qty_for_date(doc, method)
	get_opening_closing_entries(doc, method)
	doc.closing_stock = float(doc.total_litres_bottled) - float(doc.total_litres_sold_qty)
	doc.total_wastage = float(doc.total_production) - (
				float(doc.total_litres_bottled) + float(doc.total_litres_sold_qty))


def get_total_litres_sold(item_code, cumulative_qty):
	match = re.match(r"\d+(\.\d+)?", item_code)

	volume_liters = float(match.group()) if match else 0

	total_liters_for_item = float(volume_liters) * float(cumulative_qty)

	return total_liters_for_item


def calculate_total_litres_and_qty_for_date(doc, method):
	total_litres = 0
	bottled_data_dict = {}

	stock_entries = frappe.get_all('Stock Entry', filters={
		'stock_entry_type': 'Material Receipt',
		'posting_date': doc.period_start_date,
		'pending_bottle_ref': ('is', 'not set'),
		'damaged_bottle': ('is', 'not set'),
		'company': doc.company
	}, fields=['name'])

	for entry in stock_entries:
		items = frappe.get_all('Stock Entry Detail', filters={
			'parent': entry.name,
			'item_code': ['like', '%water%']
		}, fields=['item_code', 'qty'])

		for item in items:
			total_liters_for_item = get_total_litres_sold(item.item_code, item.qty)

			if item.item_code in bottled_data_dict:
				bottled_data_dict[item.item_code]['total_litres_bottled'] += total_liters_for_item
				bottled_data_dict[item.item_code]['qty'] += item.qty
			else:
				bottled_data_dict[item.item_code] = {
					'total_litres_bottled': total_liters_for_item,
					'qty': item.qty
				}

	doc.set('bottled_products', [])

	for item_code, data in bottled_data_dict.items():
		total_litres += float(data['total_litres_bottled'])
		doc.append('bottled_products', {
			'item_code': item_code,
			'total_litres_bottled': data['total_litres_bottled'],
			'cumulative_qty': data['qty']
		})

	doc.total_litres_bottled = total_litres


def get_opening_closing_entries(doc, method):
	readings = frappe.db.sql(
		"""select opening_meter_reading,closing_meter_reading,total from `tabMeter Reading`  where posting_date = %s and docstatus = 1""",
		getdate(doc.period_start_date), as_dict=1)

	if readings:
		doc.opening_meter_reading = readings[0].opening_meter_reading or 0
		doc.closing_meter_reading = readings[0].closing_meter_reading or 0
		doc.total_production = readings[0].total or 0
	else:
		doc.opening_meter_reading = 0
		doc.closing_meter_reading = 0
		doc.total_production = 0
