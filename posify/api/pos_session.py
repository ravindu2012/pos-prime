import frappe
from frappe import _
from frappe.utils import nowdate, nowtime
import json


@frappe.whitelist()
def get_opening_data():
    """Get data needed for opening a POS shift."""
    user = frappe.session.user

    # Check for existing open entry
    existing = frappe.db.get_value(
        "POS Opening Entry",
        {"user": user, "status": "Open", "docstatus": 1},
        ["name", "pos_profile", "company"],
        as_dict=True,
    )

    # Get available POS Profiles
    profiles = frappe.get_list(
        "POS Profile",
        filters={"disabled": 0},
        fields=["name", "company"],
    )

    return {
        "opening_entry": existing,
        "pos_profiles": profiles,
    }


@frappe.whitelist()
def get_shift_summary(opening_entry):
    """Get per-payment-method breakdown for closing shift.

    Uses ERPNext's built-in make_closing_entry_from_opening to get
    accurate invoice data with proper timestamp range filtering.
    """
    from erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry import (
        make_closing_entry_from_opening,
    )

    opening = frappe.get_doc("POS Opening Entry", opening_entry)
    closing_entry = make_closing_entry_from_opening(opening)

    # Build opening amounts lookup from the opening entry itself
    # (v16 doesn't prepend opening amounts into payment_reconciliation)
    opening_amounts = {
        d.mode_of_payment: d.opening_amount or 0
        for d in opening.balance_details
    }

    payment_summary = []
    for pr in closing_entry.payment_reconciliation:
        opening_amt = getattr(pr, "opening_amount", None) or opening_amounts.get(pr.mode_of_payment, 0)
        payment_summary.append(
            {
                "mode_of_payment": pr.mode_of_payment,
                "opening_amount": opening_amt,
                "sales_amount": (pr.expected_amount or 0) - opening_amt,
                "expected_amount": pr.expected_amount or 0,
            }
        )

    # v14/v15 use pos_transactions, v16 uses pos_invoices
    transactions = (
        closing_entry.get("pos_transactions")
        or closing_entry.get("pos_invoices")
        or []
    )

    return {
        "grand_total": closing_entry.grand_total,
        "net_total": closing_entry.net_total,
        "total_quantity": closing_entry.total_quantity,
        "num_invoices": len(transactions),
        "payment_summary": payment_summary,
    }


@frappe.whitelist()
def check_opening_entry(user=""):
    """Check if user has an open POS Opening Entry."""
    user = user or frappe.session.user
    entries = frappe.get_all(
        "POS Opening Entry",
        filters={"user": user, "docstatus": 1, "status": "Open"},
        fields=["name", "pos_profile", "company"],
    )
    return entries


@frappe.whitelist()
def create_opening_entry(pos_profile, company, balance_details):
    """Create a new POS Opening Entry."""
    if isinstance(balance_details, str):
        balance_details = json.loads(balance_details)

    doc = frappe.get_doc({
        "doctype": "POS Opening Entry",
        "user": frappe.session.user,
        "pos_profile": pos_profile,
        "company": company,
        "period_start_date": nowdate() + " " + nowtime(),
    })
    for detail in balance_details:
        doc.append("balance_details", {
            "mode_of_payment": detail.get("mode_of_payment"),
            "opening_amount": detail.get("opening_amount", 0),
        })
    doc.insert(ignore_permissions=True)
    doc.submit()
    return doc.as_dict()


@frappe.whitelist()
def get_pos_profile(pos_profile):
    """Get full POS Profile document with company default currency."""
    doc = frappe.get_doc("POS Profile", pos_profile)
    result = doc.as_dict()
    if not result.get("currency") and result.get("company"):
        result["currency"] = frappe.db.get_value(
            "Company", result["company"], "default_currency"
        )
    return result


@frappe.whitelist()
def close_shift(opening_entry, closing_amounts=None):
    """Create a POS Closing Entry using ERPNext's built-in logic.

    Uses make_closing_entry_from_opening which correctly fetches invoices
    by timestamp range, user, pos_profile, and excludes already-consolidated ones.
    """
    from erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry import (
        make_closing_entry_from_opening,
    )

    if isinstance(closing_amounts, str):
        closing_amounts = json.loads(closing_amounts)

    # Validate opening entry exists and is open
    if not frappe.db.exists("POS Opening Entry", opening_entry):
        frappe.throw(_("Opening entry {0} does not exist").format(opening_entry))

    opening = frappe.get_doc("POS Opening Entry", opening_entry)

    if opening.status != "Open" or opening.docstatus != 1:
        frappe.throw(_("Opening entry {0} is not open or not submitted").format(opening_entry))

    # Use ERPNext's built-in function to build the closing entry
    closing = make_closing_entry_from_opening(opening)

    # Apply user-provided closing amounts
    closing_lookup = {}
    if closing_amounts:
        for ca in closing_amounts:
            closing_lookup[ca.get("mode_of_payment")] = ca.get("closing_amount", 0)

    for pr in closing.payment_reconciliation:
        closing_amount = closing_lookup.get(pr.mode_of_payment, 0)
        pr.closing_amount = closing_amount
        pr.difference = closing_amount - (pr.expected_amount or 0)

    closing.posting_date = nowdate()
    closing.posting_time = nowtime()

    closing.insert(ignore_permissions=True)
    closing.submit()

    return {"name": closing.name, "status": "Closed"}
