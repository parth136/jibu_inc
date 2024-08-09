from __future__ import unicode_literals
import frappe
import erpnext
from frappe import _, throw
from erpnext.accounts.doctype.pos_invoice.pos_invoice import POSInvoice
from erpnext.accounts.doctype.pos_invoice.pos_invoice import *
from erpnext.accounts.doctype.loyalty_program.loyalty_program import (
	get_loyalty_program_details_with_points,
	validate_loyalty_points,
)
from frappe.utils import add_days, cint, cstr, flt, formatdate, get_link_to_form, getdate, nowdate


class CustomPOSInvoice(POSInvoice):
	def make_loyalty_point_entry(self):

		returned_amount = self.get_returned_amount()
		current_amount = flt(self.grand_total) - cint(self.loyalty_amount)
		eligible_amount = current_amount - returned_amount
		lp_details = get_loyalty_program_details_with_points(
			self.customer,
			company=self.company,
			current_transaction_amount=current_amount,
			loyalty_program=self.loyalty_program,
			expiry_date=self.posting_date,
			include_expired_entry=True,
		)
		if (
				lp_details
				and getdate(lp_details.from_date) <= getdate(self.posting_date)
				and (not lp_details.to_date or getdate(lp_details.to_date) >= getdate(self.posting_date))
		):
			collection_factor = lp_details.collection_factor if lp_details.collection_factor else 1.0
			if self.doctype == "POS Invoice":
				# points_earned = frappe.db.get_single_value('Loyalty Points Settings', 'loyalty_points_per_sale')
				points_earned = 0
				for itm in self.items:
					# get loyalty_points_per_sale for the current item
					item_points = frappe.db.get_value("Loyalty Point Settings Item", {"item_code": itm.item_code},
					                                  "loyalty_points_per_sale")
					if item_points:
						self.create_loyalty_point_entry((int(itm.stock_qty) * int(item_points)),lp_details, itm.item_code)

			else:
				points_earned = cint(eligible_amount / collection_factor)
				self.create_loyalty_point_entry(points_earned, lp_details)
			self.set_loyalty_program_tier()

	def set_loyalty_program_tier(self):
		lp_details = get_loyalty_program_details_with_points(
			self.customer,
			company=self.company,
			loyalty_program=self.loyalty_program,
			include_expired_entry=True,
		)
		frappe.db.set_value("Customer", self.customer, "loyalty_program_tier", lp_details.tier_name)

	def create_loyalty_point_entry(self, points_earned, lp_details, item_code=None):
		doc = frappe.get_doc(
			{
				"doctype": "Loyalty Point Entry",
				"company": self.company,
				"loyalty_program": lp_details.loyalty_program,
				"loyalty_program_tier": lp_details.tier_name,
				"customer": self.customer,
				"invoice_type": self.doctype,
				"invoice": self.name,
				"loyalty_points": points_earned,
				"item_code": item_code,
				"purchase_amount": self.grand_total,
				"expiry_date": add_days(self.posting_date, lp_details.expiry_duration),
				"posting_date": self.posting_date,
			}
		)
		doc.flags.ignore_permissions = 1
		doc.save()
		