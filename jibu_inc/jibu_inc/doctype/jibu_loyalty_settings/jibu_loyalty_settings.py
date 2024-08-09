# Copyright (c) 2023, Chris and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime
from frappe import _, throw


class JibuLoyaltySettings(Document):
    def before_submit(self):
        for item in self.items:
            if item.update_loyalty_points:
                # Fetch similar item from 'Loyalty Points Settings' based on item_code
                loyalty_settings = frappe.get_list("Loyalty Point Settings Item",
                                                   filters={"item_code": item.item_code},
                                                   fields=["name", "loyalty_points_per_sale"])

                if loyalty_settings:
                    # Use set_value to update the loyalty_points_per_sale directly without fetching the entire doc
                    frappe.db.set_value("Loyalty Point Settings Item", loyalty_settings[0].name,
                                        "loyalty_points_per_sale", item.new_loyalty_points_per_sale)
                    adjust_all_loyalty_points(item.new_item_price, item.new_loyalty_points_per_sale, item.loyalty_points_per_sale, item.item_code)



def get_active_loyalty_programs(current_date):
    loyalty_programs = frappe.get_all('Loyalty Program',
                                      filters=lambda d: (d.to_date > current_date) or d.to_date == None,
                                      fields=['name'])
    return loyalty_programs


@frappe.whitelist()
def adjust_all_loyalty_points(new_price, new_points, old_points, item_code):
    # Fetch all active loyalty programs (those whose to_date is greater than today)
    current_date = datetime.now().date()

    loyalty_programs = frappe.get_all('Loyalty Program', filters={'to_date': ['>', current_date]}, fields=['name'])

    for program in loyalty_programs:
        adjust_loyalty_points_for_program_members(program.name, new_price, new_points, old_points, item_code)


def adjust_loyalty_points_for_program_members(program_name, new_price, new_points, old_points, item_code):
    # Fetch customers enrolled in the specified loyalty program
    customers_in_program = frappe.get_all('Customer', filters={'loyalty_program': program_name}, fields=['name'])

    for customer in customers_in_program:
        adjust_loyalty_points(customer.name, program_name, new_price, new_points, old_points, item_code)


def adjust_loyalty_points(customer_name, program_name, new_price, new_points, old_points, item_code):
    # Get only the unredeemed loyalty entries for the customer and where the loyalty_program matches
    loyalty_entries = frappe.get_all('Loyalty Point Entry',
                                     filters={
                                         'customer': customer_name,
                                         'loyalty_program': program_name,
                                         'redeem_against': ['is', 'not set'],
	                                     'item_code': item_code
                                     },
                                     fields=['name', 'loyalty_points'])

    for entry in loyalty_entries:
        # Check if entry.points is a multiple of old_points
        # if float(entry.loyalty_points) % float(old_points) == 0:
            # Calculate adjusted points
        adjusted_points = (float(entry.loyalty_points) / float(old_points)) * float(new_points)
            # Update the Loyalty Point Entry with the adjusted points
        frappe.db.set_value('Loyalty Point Entry', entry.name, 'loyalty_points', adjusted_points)
