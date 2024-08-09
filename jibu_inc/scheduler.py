import frappe
from datetime import datetime
from frappe.utils import nowdate, add_days, getdate, add_months
from frappe import _


def update_time_since_last_purchase():
    customers = frappe.get_all("Customer", fields=["name", "last_purchase_date"])

    for customer in customers:
        last_purchase_date = customer.last_purchase_date
        status = "Lead"
        if last_purchase_date:
            last_purchase_date = getdate(last_purchase_date)
            current_date = getdate(nowdate())
            time_difference = current_date - last_purchase_date
            hours_difference = time_difference.total_seconds() / (60 * 60)

            if hours_difference < 24:
                time_since_last_purchase = f"{int(hours_difference)} hours"
                status = "Active"
            else:
                days_difference = time_difference.days
                time_since_last_purchase = f"{days_difference} days"
                if days_difference <= 0:
                    status = "Lead"
                elif days_difference <= 30:
                    status = "Active"
                elif days_difference <= 60:
                    status = "Passive"
                elif days_difference <= 90:
                    status = "Inactive"
                else:
                    status = "Churn"

            frappe.db.set_value("Customer", customer.name, "status", status)

            frappe.db.set_value(
                "Customer", customer.name, "time_since_last_purchase", time_since_last_purchase
            )
            frappe.db.commit()
        else:
            frappe.db.set_value("Customer", customer.name, "status", "Lead")
            frappe.db.commit()


def update_customer_status():
    # Get today's date
    today = nowdate()

    # Get all customers
    customers = frappe.get_all("Customer", fields=["name", "last_purchase_date"])

    for customer in customers:
        status = None
        last_purchase_date = getdate(customer.last_purchase_date)  # Convert to datetime

        # Calculate dates for comparison
        one_month_ago = getdate(add_months(today, -1))  # Convert to datetime
        two_months_ago = getdate(add_months(today, -2))  # Convert to datetime
        three_months_ago = getdate(add_months(today, -3))  # Convert to datetime

        # Determine status based on purchase history
        if not last_purchase_date:
            status = "Lead"
        elif last_purchase_date > one_month_ago:
            status = "Active"
        elif one_month_ago >= last_purchase_date > two_months_ago:
            status = "Passive"
        elif two_months_ago >= last_purchase_date > three_months_ago:
            status = "Inactive"
        elif last_purchase_date <= three_months_ago:
            status = "Churn"

        # Update the customer status
        frappe.db.set_value("Customer", customer.name, "status", status)

    # Commit changes
    frappe.db.commit()


def enqueue_update_pending_bill_for_all_companies():
    companies = frappe.get_all('Company', fields=['name'])

    for company in companies:
        customers = frappe.get_all('Customer', filters={'disabled': 0}, fields=['name'])

        for customer in customers:
            update_pending_bill(customer.name, company.name)

def update_pending_bill(customer, company):
    doc = frappe.get_doc('Customer', customer)

    sales_invoices = frappe.get_all('Sales Invoice',
                                    filters={
                                        'customer': customer,
                                        'docstatus': 1,
                                        'company': company,
                                        'outstanding_amount': ['>', 0]
                                    },
                                    fields=['outstanding_amount'])

    total_outstanding = sum(invoice.outstanding_amount for invoice in sales_invoices)

    frappe.db.set_value('Customer', customer, 'outstanding_amount', total_outstanding)

    # Update the customer credit status
    if total_outstanding > 0:
        frappe.db.set_value('Customer', customer, 'credit_status', 'Debt')
    else:
        frappe.db.set_value('Customer', customer, 'credit_status', 'Paid')
