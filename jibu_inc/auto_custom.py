import frappe
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from frappe.utils import today, nowdate, add_days
from erpnext.accounts.doctype.loyalty_program.loyalty_program import get_loyalty_program_details_with_points
from datetime import datetime
import csv
import os

def get_pos_invoices():
    thirty_days_ago = add_days(nowdate(), -32)
    return frappe.db.sql(f'''SELECT name, customer, posting_date FROM `tabPOS Invoice`
                             WHERE posting_date >= '{thirty_days_ago}'
                              AND posting_date <= '{nowdate()}'
                             AND docstatus = 1
                             ORDER BY posting_date DESC''', as_dict=1)

import frappe
from frappe.utils import add_days, nowdate
from datetime import datetime
from collections import defaultdict, Counter

def calculate_average_purchase_time_and_last_date(invoices):
    purchase_intervals = defaultdict(list)
    last_purchase_date = {}
    processed_dates = defaultdict(Counter)
    default_avg_days = 14  # Default average days if only one invoice

    current_date = datetime.strptime(nowdate(), '%Y-%m-%d').date()

    for invoice in invoices:
        customer = invoice['customer']
        date = invoice['posting_date']

        # Skip if invoice is older than 30 days
        if add_days(date, 30) < current_date:
            continue

        # Ensure we are handling the date in the correct format
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()

        # Update the last purchase date if this is the first encountered invoice for this customer
        if customer not in last_purchase_date:
            last_purchase_date[customer] = date

        # Skip if we have already processed an invoice for this customer on this date
        if processed_dates[customer][date] > 0:
            continue

        # Calculate interval only if this is not the first invoice for this customer
        if customer in processed_dates and date < last_purchase_date[customer]:
            interval = (last_purchase_date[customer] - date).days
            if interval > 0:  # Only consider positive intervals
                purchase_intervals[customer].append(interval)

        # Mark the date as processed for this customer
        processed_dates[customer][date] += 1

    # Calculate the average time
    average_time = {}
    for customer in last_purchase_date:
        if purchase_intervals[customer]:
            average_time[customer] = sum(purchase_intervals[customer]) / len(purchase_intervals[customer])
        else:
            # Set a default of 14 days if only one invoice
            average_time[customer] = default_avg_days

    return average_time, last_purchase_date


def update_customer_next_purchase_date(average_time, last_purchase_date):
    for customer, avg_days in average_time.items():
        next_purchase_date = last_purchase_date[customer] + timedelta(days=avg_days)
        customer_doc = frappe.get_doc("Customer", customer)
        customer_doc.next_projected_purchase_date = next_purchase_date
        customer_doc.average_purchase_time = avg_days
        customer_doc.flags.ignore_permissions = 1
        customer_doc.flags.ignore_mandatory = 1
        customer_doc.save()


@frappe.whitelist()
def calculate_average_and_next_purchase_date():
    invoices = get_pos_invoices()
    average_time, last_purchase_date = calculate_average_purchase_time_and_last_date(invoices)
    update_customer_next_purchase_date(average_time, last_purchase_date)


def get_customers_due_today():
    current_date = nowdate()
    customers_due_today = frappe.get_all('Customer',
                                         fields=['name', 'customer_name', 'mobile_no'],
                                         filters={'next_projected_purchase_date': current_date})

    return [{'name': customer.customer_name, 'mobile_no': customer.mobile_no} for customer in customers_due_today]


def get_customers_due_for_purchase_today():
    current_date = nowdate()
    customers_due_today = []

    invoices = get_pos_invoices()
    average_time, last_purchase_date = calculate_average_purchase_time_and_last_date(invoices)

    for customer, avg_days in average_time.items():
        next_purchase_date = last_purchase_date[customer] + timedelta(days=avg_days)
        if next_purchase_date == current_date:
            customers_due_today.append(customer)

    return customers_due_today


def get_customer_contact_details(customers):
    customer_details = []
    for customer in customers:
        customer_doc = frappe.get_doc("Customer", customer)
        name = customer_doc.customer_name
        mobile_no = customer_doc.mobile_no
        customer_details.append({'name': name, 'mobile_no': mobile_no})

    return customer_details


def get_sales_managers():
    sales_managers = []
    sales_manager_role = "Sales Manager"  # Adjust if your role name is different

    users_with_role = frappe.get_all('Has Role', fields=['parent'], filters={'role': sales_manager_role})
    for user in users_with_role:
        if frappe.db.exists('User', user.parent):  # Check if the user exists in User doctype
            sales_managers.append(user.parent)

    return sales_managers


def send_system_notification(customer_details, sales_managers):
    subject = "Customers Due for Purchase Today"
    message = "Customers due for purchase today:\n\n"
    for detail in customer_details:
        message += f"{detail['name']} - {detail['mobile_no']}\n"

    for manager in sales_managers:
        notification = {
            'type': 'Alert',
            'subject': subject,
            'email_content': message,
            'for_user': manager
        }
        doc = frappe.get_doc(dict(doctype='Notification Log', **notification))
        doc.flags.ignore_permissions = 1
        doc.save()


@frappe.whitelist()
def send_notification_for_daily_projected_purchases():
    customer_details = get_customers_due_today()
    sales_managers = get_sales_managers()
    send_system_notification(customer_details, sales_managers)


def check_stock_levels_against_safety_stock():
    items_below_safety_stock = []

    items = frappe.get_all('Item', fields=['name', 'item_name', 'safety_stock'],
                           filters={'disabled': 0, 'is_stock_item': 1})
    for item in items:
        total_stock_balance = frappe.db.sql("""
            SELECT SUM(actual_qty) FROM `tabBin` 
            WHERE item_code = %s""", item.name, as_list=True)[0][0] or 0

        if total_stock_balance <= item.safety_stock:
            items_below_safety_stock.append(item)

    return items_below_safety_stock


def send_notification_to_sales_managers(items_below_safety_stock, sales_managers):
    if not items_below_safety_stock:
        return

    subject = "Items Below Safety Stock"
    message = "The following items have reached or are below the safety stock level:\n"
    for item in items_below_safety_stock:
        message += f"{item.item_name} (Code: {item.name}) \n"

    for manager in sales_managers:
        notification = {
            'type': 'Alert',
            'subject': subject,
            'email_content': message,
            'for_user': manager
        }
        doc = frappe.get_doc(dict(doctype='Notification Log', **notification))
        doc.flags.ignore_permissions = 1
        doc.save()


@frappe.whitelist()
def send_notification_for_stock_levels():
    sales_managers = get_sales_managers()
    items_below_safety_stock = check_stock_levels_against_safety_stock()
    send_notification_to_sales_managers(items_below_safety_stock, sales_managers)


def update_loyalty_points_on_invoice_submission(doc, method):
    if doc.docstatus == 1:
        loyalty_points = get_customer_loyalty_points(doc.customer)
        doc.db_set('current_loyalty_points', loyalty_points)


def get_customer_loyalty_points(customer):
    customer_loyalty_program = frappe.db.get_value("Customer", customer, "loyalty_program")

    if customer_loyalty_program:
        loyalty_program_details = get_loyalty_program_details_with_points(customer, customer_loyalty_program)
        return int(loyalty_program_details.get("loyalty_points"))

    return 0


@frappe.whitelist()
def populate_translations():
    try:
        app_path = frappe.get_app_path('jibu_inc')
        csv_file_path = os.path.join(app_path, "translations", 'translation.csv')

        with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)

            for row in csv_reader:
                try:
                    language = row['Language']
                    source_text = row['Source Text']
                    translated_text = row['Translated Text']

                    existing_translation = frappe.db.exists('Translation',
                                                            {'source_text': source_text, 'language': language})

                    if not existing_translation:
                        new_translation = frappe.get_doc({
                            'doctype': 'Translation',
                            'source_text': source_text,
                            'translated_text': translated_text,
                            'language': language
                        })
                        new_translation.insert(ignore_permissions=True)
                        frappe.db.commit()
                except Exception as e:
                    frappe.log_error(f"Error processing row: {row}\nError: {e}")
    except Exception as e:
        frappe.log_error(f"Error in populate_translations: {e}")
