import frappe
from datetime import datetime
from frappe import _, throw


def get_active_loyalty_programs(current_date):
    loyalty_programs = frappe.get_all('Loyalty Program',
                                      filters=lambda d: (d.to_date > current_date) or d.to_date == None,
                                      fields=['name'])
    return loyalty_programs


@frappe.whitelist()
def adjust_all_loyalty_points(new_price, new_points, old_points):
    # Fetch all active loyalty programs (those whose to_date is greater than today)
    current_date = datetime.now().date()

    # Fetch all active loyalty programs (those whose to_date is greater than today or to_date is None/empty)
    # # loyalty_programs = frappe.get_all('Loyalty Program',
    # #                                   filters="""to_date > '{0}' OR to_date IS NULL""".format(current_date),
    # #                                   fields=['name'])
    # loyalty_programs = get_active_loyalty_programs(current_date)
    # frappe.throw(loyalty_programs)
    loyalty_programs = frappe.get_all('Loyalty Program', filters={'to_date': ['>', current_date]}, fields=['name'])

    for program in loyalty_programs:
        adjust_loyalty_points_for_program_members(program.name, new_price, new_points, old_points)


def adjust_loyalty_points_for_program_members(program_name, new_price, new_points, old_points):
    # Fetch customers enrolled in the specified loyalty program
    customers_in_program = frappe.get_all('Customer', filters={'loyalty_program': program_name}, fields=['name'])

    for customer in customers_in_program:
        adjust_loyalty_points(customer.name, program_name, new_price, new_points, old_points)


def adjust_loyalty_points_old(customer_name, program_name, new_price, new_points, old_points):
    # Get only the unredeemed loyalty entries for the customer and where the loyalty_program matches
    loyalty_entries = frappe.get_all('Loyalty Point Entry',
                                     filters={
                                         'customer': customer_name,
                                         'loyalty_program': program_name,
                                         'redeemed_against': ['is', 'not set']
                                     },
                                     fields=['name', 'points'])
    # loyalty_entries = frappe.get_all('Loyalty Point Entry',
    #                                  filters={'customer': customer_name, 'loyalty_program': program_name,
    #                                           'redeemed_against': 0}, fields=['name', 'points'])

    for entry in loyalty_entries:
        # Logic to calculate the adjusted points
        adjusted_points = entry.points * (new_points / new_price)

        # Update the Loyalty Point Entry
        frappe.db.set_value('Loyalty Point Entry', entry.name, 'points', adjusted_points)


def adjust_loyalty_points(customer_name, program_name, new_price, new_points, old_points):
    # Get only the unredeemed loyalty entries for the customer and where the loyalty_program matches
    loyalty_entries = frappe.get_all('Loyalty Point Entry',
                                     filters={
                                         'customer': customer_name,
                                         'loyalty_program': program_name,
                                         'redeem_against': ['is', 'not set']
                                     },
                                     fields=['name', 'loyalty_points'])

    for entry in loyalty_entries:
        # Check if entry.points is a multiple of old_points
        if float(entry.loyalty_points) % float(old_points) == 0:
            # Calculate adjusted points
            adjusted_points = (float(entry.loyalty_points) / float(old_points)) * float(new_points)
            # Update the Loyalty Point Entry with the adjusted points
            frappe.db.set_value('Loyalty Point Entry', entry.name, 'loyalty_points', adjusted_points)
