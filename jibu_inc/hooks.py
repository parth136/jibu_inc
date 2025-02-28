from . import __version__ as app_version

app_name = "jibu_inc"
app_title = "Jibu Inc"
app_publisher = "Chris"
app_description = "Jibu Inc Custom Application"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@pointershub.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/jibu_inc/css/jibu_inc.css"
app_include_js = "/assets/jibu_inc/js/pos_jibu.js"
# include js, css files in header of web template
# web_include_css = "/assets/jibu_inc/css/jibu_inc.css"
# web_include_js = "/assets/jibu_inc/js/jibu_inc.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "jibu_inc/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
#doctype_js = {"POS Closing Entry" : "public/js/pos_closing_entry.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "jibu_inc.install.before_install"
# after_install = "jibu_inc.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "jibu_inc.uninstall.before_uninstall"
# after_uninstall = "jibu_inc.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "jibu_inc.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }
override_doctype_class = {
    # "Sales Invoice": "jibu_inc.overrides.sales_invoice.CustomSalesInvoice",
    "POS Invoice": "jibu_inc.overrides.pos_invoice.CustomPOSInvoice"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"POS Closing Entry": {
		"before_save": "jibu_inc.doctype_functions.pos_closing_entry.update_pos_products"
	},
	"POS Invoice": {
	    "on_submit": "jibu_inc.auto_custom.update_loyalty_points_on_invoice_submission"
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"hourly": [
		"jibu_inc.scheduler.update_time_since_last_purchase"
	],
	"daily": [
		"jibu_inc.scheduler.enqueue_update_pending_bill_for_all_companies",
		"jibu_inc.auto_custom.calculate_average_and_next_purchase_date",
		"jibu_inc.auto_custom.send_notification_for_daily_projected_purchases",
		"jibu_inc.auto_custom.send_notification_for_stock_levels"
	],
}
# scheduler_events = {
# 	"all": [
# 		"jibu_inc.tasks.all"
# 	],
# 	"daily": [
# 		"jibu_inc.tasks.update_customer_status"
# 	],

# 	"weekly": [
# 		"jibu_inc.tasks.weekly"
# 	]
# 	"monthly": [
# 		"jibu_inc.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "jibu_inc.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "jibu_inc.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "jibu_inc.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"jibu_inc.auth.validate"
# ]

# Translation
# --------------------------------

# Make link fields search translated document names for these DocTypes
# Recommended only for DocTypes which have limited documents with untranslated names
# For example: Role, Gender, etc.
# translated_search_doctypes = []

fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "name",
                "in",
                (
                    "POS Closing Entry-products_details",
	                "POS Closing Entry-pos_products",
	                "Stock Entry-pending_bottle_ref",
	                "Stock Entry-customer",
                ),
            ]
        ],
    },
]

invoice_doctypes = ["Expenses Entry"]

accounting_dimension_doctypes = [
	"Expenses Entry",
	"Expenses Item"
]

bank_reconciliation_doctypes = ["Expenses Entry"]

after_migrate = [
    "jibu_inc.auto_custom.populate_translations"
]
after_install = "jibu_inc.auto_custom.populate_translations"