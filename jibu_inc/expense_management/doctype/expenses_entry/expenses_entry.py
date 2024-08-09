# Copyright (c) 2023, Pointershub Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt
from erpnext.accounts.general_ledger import make_gl_entries, make_reverse_gl_entries
from frappe.utils import add_days, add_months, add_years, getdate, nowdate, flt, now, time_diff_in_hours, format_duration
from datetime import datetime
from erpnext.controllers.accounts_controller import AccountsController
from erpnext.accounts.utils import get_account_currency, get_fiscal_years, validate_fiscal_year
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)

class ExpensesEntry(Document):
    @frappe.whitelist()
    def get_mode_of_payment_details(self):
        mode_of_payment_doc = frappe.get_doc("Mode of Payment", self.mode_of_payment)

        payment_account = None
        for entry in mode_of_payment_doc.accounts:
            if entry.company == self.company:
                payment_account = entry.default_account
                break

        if payment_account:
            payment_currency = frappe.db.get_value("Account", payment_account, "account_currency")
            return {
                'payment_account': payment_account,
                'payment_currency': payment_currency
            }
        return {}

    def validate(self):
        self.check_currency_mismatch()
        self.get_default_cost_center()

    def get_default_cost_center(self):
        if not self.default_cost_center:
            self.default_cost_center = frappe.db.get_value("Company", self.company, "cost_center")

        for item in self.get("expenses"):
            if not item.cost_center:
                item.cost_center = self.default_cost_center

    def on_submit(self):
        # self.create_gl_entries()
        self.make_gl_entries()

    def on_cancel(self):
        self.ignore_linked_doctypes = (
            "GL Entry",
        )
        self.make_gl_entries(cancel=1)

    def check_currency_mismatch(self):
        for item in self.expenses:
            if self.payment_currency != item.account_currency:
                frappe.throw(_("Currency mismatch between Expense Account '{0}' and Debit Account '{1}'").format(item.account_currency,

                                                                                                        self.payment_currency))
    def create_gl_entries(self):
        gl_entries = []
        credit_account = self.liability_or_asset_account

        for item in self.expenses:
            debit_gl_entry = {
                "voucher_type": self.doctype,
                "voucher_no": self.name,
                "account": item.account,
                "party_type": item.party_type if item.party_type else None,
                "party": item.party if item.party else None,
                "against_account": credit_account,
                "debit": flt(item.amount),
                "credit": 0,
                # "project": item.project,
                "cost_center": item.cost_center if item.cost_center else None,
                "posting_date": self.posting_date
            }

            # Credit entry
            credit_gl_entry = {
                "voucher_type": self.doctype,
                "voucher_no": self.name,
                "account": credit_account,
                "party_type": item.party_type if item.party_type else None,
                "party": item.party if item.party else None,
                "against_account": item.account,
                "debit": 0,
                "credit": flt(item.amount),
                # "project": item.project,
                "cost_center": item.cost_center if item.cost_center else None,
                "posting_date": self.posting_date

            }

            gl_entries.extend([debit_gl_entry, credit_gl_entry])
            make_gl_entries(gl_entries)

    def make_gl_entries(self, cancel=False):
        gl_entries = self.get_gl_entries()
        make_gl_entries(gl_entries, cancel)

    def get_gl_entries(self):
        gl_entries = []
        credit_account = self.liability_or_asset_account

        if self.get("expenses"):
            for item in self.expenses:
                gl_entries.append(
                    self.get_gl_dict(
                        {
                            "account": credit_account,
                            "credit": item.amount,
                            "credit_in_account_currency": item.amount,
                            "against": item.account,
                            "voucher_type": "Expenses Entry",
                            "voucher_no": self.name,
                            "cost_center": item.cost_center,
                            "posting_date": getdate(),
                            "company": self.company,
                            "party_type": item.party_type if item.party_type else None,
                            "party": item.party if item.party else None,
                        },
                        item=self,
                    )
                )

                gl_entries.append(
                    self.get_gl_dict(
                        {
                            "account": item.account,
                            "debit": item.amount,
                            "debit_in_account_currency": item.amount,
                            "against": credit_account,
                            "voucher_type": "Expenses Entry",
                            "voucher_no": self.name,
                            "cost_center": item.cost_center,
                            "posting_date": getdate(),
                            "against_voucher_type": "Expenses Entry",
                            "against_voucher": self.name,
                            "company": self.company,
                            "party_type": item.party_type if item.party_type else None,
                            "party": item.party if item.party else None,
                        },
                        item=self,
                    )
                )

            return gl_entries

    def get_gl_dict(self, args, account_currency=None, item=None):
        """this method populates the common properties of a gl entry record"""

        posting_date = args.get('posting_date') or self.get('posting_date')
        fiscal_years = get_fiscal_years(posting_date, company=self.company)
        if len(fiscal_years) > 1:
            frappe.throw(_("Multiple fiscal years exist for the date {0}. Please set company in Fiscal Year").format(
                formatdate(posting_date)))
        else:
            fiscal_year = fiscal_years[0][0]

        gl_dict = frappe._dict({
            'company': self.company,
            'posting_date': posting_date,
            'fiscal_year': fiscal_year,
            'voucher_type': self.doctype,
            'voucher_no': self.name,
            'remarks': self.get("remarks") or self.get("remark"),
            'debit': 0,
            'credit': 0,
            'debit_in_account_currency': 0,
            'credit_in_account_currency': 0,
            'is_opening': self.get("is_opening") or "No",
            'party_type': None,
            'party': None,
            'project': self.get("project"),
            'post_net_value': args.get('post_net_value')
        })

        accounting_dimensions = get_accounting_dimensions()
        dimension_dict = frappe._dict()

        for dimension in accounting_dimensions:
            dimension_dict[dimension] = self.get(dimension)
            if item and item.get(dimension):
                dimension_dict[dimension] = item.get(dimension)

        gl_dict.update(dimension_dict)
        gl_dict.update(args)

        return gl_dict

    def validate_account_currency(self, account, account_currency=None):
        valid_currency = [self.company_currency]
        if self.get("currency") and self.currency != self.company_currency:
            valid_currency.append(self.currency)

        if account_currency not in valid_currency:
            frappe.throw(_("Account {0} is invalid. Account Currency must be {1}")
                         .format(account, (' ' + _("or") + ' ').join(valid_currency)))
