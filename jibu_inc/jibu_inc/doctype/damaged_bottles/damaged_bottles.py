# Copyright (c) 2023, Chris and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DamagedBottles(Document):
	@frappe.whitelist()
	def get_bottle_warehouse(self):
		warehouse = frappe.db.get_value("Bottles Warehouse Settings", {"company": self.company}, "default_warehouse")
		return warehouse

	def before_save(self):
		self.warehouse = self.get_bottle_warehouse()

	def before_submit(self):
		if not self.warehouse:
			self.warehouse = self.get_bottle_warehouse()

		for d in self.get("items"):
			create_material_issue(self.name, d.type_of_damage, d.item_code, d.qty, self.warehouse)


def create_material_issue(damaged_bottle, type_of_damage, item_code, qty, warehouse):
	doc = frappe.get_doc({
		'doctype': 'Stock Entry',
		'stock_entry_type': 'Material Issue',
		'damaged_bottle': damaged_bottle,
		'type_of_damage': type_of_damage,
		'items': [{
			'item_code': item_code,
			'qty': qty,
			's_warehouse': warehouse
		}]
	})
	doc.insert()
	doc.submit()
