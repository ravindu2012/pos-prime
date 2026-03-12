# Copyright (c) 2026, Ravindu Gajanayaka
# Licensed under GPLv3. See license.txt

import frappe
from frappe import _
from frappe.utils import nowdate, nowtime
import json
import erpnext
from pos_prime.api._utils import validate_pos_access


@frappe.whitelist()
def get_opening_data():
    """Get data needed for opening a POS shift."""
    validate_pos_access()
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
    validate_pos_access()
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
        row_opening = getattr(pr, "opening_amount", None)
        if row_opening:
            # v14/v15: opening_amount is prepopulated on the row,
            # and expected_amount = opening + sales
            opening_amt = row_opening
            sales_amt = (pr.expected_amount or 0) - opening_amt
        else:
            # v16: opening_amount is 0 on the row,
            # and expected_amount = sales only (opening not included)
            opening_amt = opening_amounts.get(pr.mode_of_payment, 0)
            sales_amt = pr.expected_amount or 0

        payment_summary.append(
            {
                "mode_of_payment": pr.mode_of_payment,
                "opening_amount": opening_amt,
                "sales_amount": sales_amt,
                "expected_amount": opening_amt + sales_amt,
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
    validate_pos_access()
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
    validate_pos_access(pos_profile)
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
    validate_pos_access(pos_profile)
    doc = frappe.get_doc("POS Profile", pos_profile)
    result = doc.as_dict()
    if not result.get("currency") and result.get("company"):
        result["currency"] = frappe.db.get_value(
            "Company", result["company"], "default_currency"
        )

    # Normalize v14/v15/v16 field differences so frontend reads consistent keys:
    # v16 renamed disable_grand_total_to_default_mop → set_grand_total_to_default_mop (inverted)
    if "set_grand_total_to_default_mop" in result and "disable_grand_total_to_default_mop" not in result:
        result["disable_grand_total_to_default_mop"] = not result["set_grand_total_to_default_mop"]
    # v14: field doesn't exist at all — default to False (pre-fill enabled)
    if "disable_grand_total_to_default_mop" not in result:
        result["disable_grand_total_to_default_mop"] = False

    # Expose ERPNext major version so frontend can toggle version-specific features
    result["erpnext_version"] = int(erpnext.__version__.split(".")[0])

    return result


@frappe.whitelist()
def get_branding(company=""):
    """Get app logo and favicon for the POS UI.

    Reads from Website Settings (app_logo, favicon) with fallback to Company logo.
    Uses frappe.db.get_single_value so no doctype read permission is needed.
    """
    validate_pos_access()
    app_logo = frappe.db.get_single_value("Website Settings", "app_logo") or ""
    favicon = frappe.db.get_single_value("Website Settings", "favicon") or ""

    company_logo = ""
    company_abbr = ""
    company_name = ""
    if company:
        comp_data = frappe.db.get_value(
            "Company", company, ["company_logo", "abbr", "company_name"], as_dict=True
        )
        if comp_data:
            company_logo = comp_data.company_logo or ""
            company_abbr = comp_data.abbr or ""
            company_name = comp_data.company_name or company

    return {
        "app_logo": app_logo,
        "favicon": favicon,
        "company_logo": company_logo,
        "company_abbr": company_abbr,
        "company_name": company_name,
    }


@frappe.whitelist()
def get_invoice_option_lists():
    """Get dropdown options for Invoice Options panel.

    Returns lists of Sales Partners, Projects, Shipping Rules,
    Terms and Conditions, and Payment Terms Templates.
    Uses frappe.get_all with ignore_permissions so non-admin POS users
    don't need direct read access to these doctypes.
    """
    validate_pos_access()
    return {
        "sales_partners": frappe.get_all(
            "Sales Partner", fields=["name"], limit_page_length=100,
            ignore_permissions=True, order_by="name asc",
        ),
        "projects": frappe.get_all(
            "Project", filters={"status": "Open"}, fields=["name"],
            limit_page_length=100, ignore_permissions=True, order_by="name asc",
        ),
        "shipping_rules": frappe.get_all(
            "Shipping Rule", fields=["name"], limit_page_length=50,
            ignore_permissions=True, order_by="name asc",
        ),
        "terms_and_conditions": frappe.get_all(
            "Terms and Conditions", fields=["name"], limit_page_length=50,
            ignore_permissions=True, order_by="name asc",
        ),
        "payment_terms_templates": frappe.get_all(
            "Payment Terms Template", fields=["name"], limit_page_length=50,
            ignore_permissions=True, order_by="name asc",
        ),
    }


@frappe.whitelist()
def get_user_info():
    """Get current user's display info (full name and avatar).

    Uses frappe.db.get_value so no User doctype read permission is needed.
    """
    validate_pos_access()
    user = frappe.session.user
    data = frappe.db.get_value(
        "User", user, ["full_name", "user_image"], as_dict=True
    )
    return {
        "full_name": data.full_name if data else user,
        "user_image": data.user_image if data else None,
    }


@frappe.whitelist()
def get_opening_entry_detail(entry_name):
    """Get POS Opening Entry status details for kiosk initialization.

    Returns essential fields without requiring direct doctype read permission.
    """
    validate_pos_access()
    if not frappe.db.exists("POS Opening Entry", entry_name):
        frappe.throw(_("POS Opening Entry {0} does not exist").format(entry_name))

    data = frappe.db.get_value(
        "POS Opening Entry",
        entry_name,
        ["name", "docstatus", "status", "pos_profile", "company", "user"],
        as_dict=True,
    )
    return data


@frappe.whitelist()
def close_shift(opening_entry, closing_amounts=None):
    """Create a POS Closing Entry using ERPNext's built-in logic.

    Uses make_closing_entry_from_opening which correctly fetches invoices
    by timestamp range, user, pos_profile, and excludes already-consolidated ones.
    """
    validate_pos_access()
    from erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry import (
        make_closing_entry_from_opening,
    )

    if isinstance(closing_amounts, str):
        closing_amounts = json.loads(closing_amounts)

    # Validate opening entry exists
    if not frappe.db.exists("POS Opening Entry", opening_entry):
        frappe.throw(_("Opening entry {0} does not exist").format(opening_entry))

    opening = frappe.get_doc("POS Opening Entry", opening_entry)

    # If opening entry is already closed, check if a closing entry exists
    # (handles retries after partial failures like scheduler being inactive)
    if opening.status != "Open" or opening.docstatus != 1:
        existing_closing = frappe.db.get_value(
            "POS Closing Entry",
            {"pos_opening_entry": opening_entry, "docstatus": 1},
            "name",
        )
        if existing_closing:
            return {"name": existing_closing, "status": "Closed"}
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

    try:
        closing.submit()
    except Exception:
        # submit() saves the doc before on_submit hooks run, so the closing
        # entry may already be submitted even if a hook (e.g. invoice
        # consolidation / scheduler check) fails. Reload and check.
        closing.reload()
        if closing.docstatus == 1:
            # Shift closed successfully — the hook error is non-fatal
            frappe.clear_messages()
            return {"name": closing.name, "status": "Closed"}
        raise

    return {"name": closing.name, "status": "Closed"}
