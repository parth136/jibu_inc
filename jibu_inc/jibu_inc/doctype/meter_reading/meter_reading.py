# Copyright (c) 2024, Chris and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MeterReading(Document):
	def before_insert(self):
		self.set_meter_reading()
		self.validate_last_closing_reading()

	def before_submit(self):
		self.set_meter_reading()
		self.validate_meter_reading()

	def before_save(self):
		self.validate_last_closing_reading()

	def set_meter_reading(self):
		if self.is_new():
			if not self.opening_meter_reading:
				frappe.throw("Please Input an Opening Meter Reading")
		else:
			if not self.opening_meter_reading and not self.closing_meter_reading:
				frappe.throw("Please Input an Opening Meter Reading and Closing Meter Reading")
			elif not self.opening_meter_reading:
				frappe.throw("Please Input an Opening Meter Reading")
			elif not self.closing_meter_reading:
				frappe.throw("Please Input a Closing Meter Reading")

	def validate_meter_reading(self):
		if float(self.opening_meter_reading) > float(self.closing_meter_reading):
			frappe.throw("Opening Meter Reading cannot be greater than Closing Meter Reading")

		self.validate_last_closing_reading()

	def validate_last_closing_reading(self):
		last_meter_reading = frappe.db.sql("""
										SELECT closing_meter_reading FROM `tabMeter Reading` 
										WHERE company = %s AND name != %s ORDER BY creation DESC LIMIT 1""",
		                                   (self.company, self.name), as_dict=True)
		if last_meter_reading:
			if float(last_meter_reading[0].closing_meter_reading) > float(self.opening_meter_reading):
				reading_value = last_meter_reading[0].closing_meter_reading
				frappe.throw(f"Opening Meter Reading cannot be less than the last Closing Meter Reading of {reading_value}")
