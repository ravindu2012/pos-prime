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

    Returns expected amounts calculated from actual payment entries
    in POS Invoices during this shift.
    """
    opening = frappe.get_doc("POS Opening Entry", opening_entry)

    # Get all POS Invoices for this shift
    invoices = frappe.get_list(
        "POS Invoice",
        filters={
            "pos_profile": opening.pos_profile,
            "owner": frappe.session.user,
            "docstatus": 1,
            "posting_date": [">=", str(opening.period_start_date).split(" ")[0]],
        },
        fields=["name", "grand_total", "net_total", "total_qty"],
    )

    grand_total = sum(inv.grand_total for inv in invoices)
    net_total = sum(inv.net_total for inv in invoices)
    total_qty = sum(inv.total_qty for inv in invoices)

    # Get actual payment totals per mode from invoice payments
    invoice_names = [inv.name for inv in invoices]
    payment_totals = {}

    if invoice_names:
        payments = frappe.db.sql(
            """
            SELECT mode_of_payment, SUM(amount) as total_amount
            FROM `tabSales Invoice Payment`
            WHERE parent IN %(invoices)s
            GROUP BY mode_of_payment
            """,
            {"invoices": invoice_names},
            as_dict=True,
        )
        for p in payments:
            payment_totals[p.mode_of_payment] = p.total_amount or 0

    # Build per-payment-method summary
    payment_summary = []
    for bd in opening.balance_details:
        mode = bd.mode_of_payment
        opening_amount = bd.opening_amount or 0
        sales_amount = payment_totals.pop(mode, 0)
        expected = opening_amount + sales_amount

        payment_summary.append(
            {
                "mode_of_payment": mode,
                "opening_amount": opening_amount,
                "sales_amount": sales_amount,
                "expected_amount": expected,
            }
        )

    # Add any payment modes that were used but not in opening balance
    for mode, amount in payment_totals.items():
        payment_summary.append(
            {
                "mode_of_payment": mode,
                "opening_amount": 0,
                "sales_amount": amount,
                "expected_amount": amount,
            }
        )

    return {
        "grand_total": grand_total,
        "net_total": net_total,
        "total_quantity": total_qty,
        "num_invoices": len(invoices),
        "payment_summary": payment_summary,
    }


def _get_shift_data(opening):
    """Fetch fresh shift summary data for closing.

    This is an internal helper that computes summary data directly,
    avoiding the race condition of calling get_shift_summary separately.
    """
    invoices = frappe.get_list(
        "POS Invoice",
        filters={
            "pos_profile": opening.pos_profile,
            "owner": frappe.session.user,
            "docstatus": 1,
            "posting_date": [">=", str(opening.period_start_date).split(" ")[0]],
        },
        fields=["name", "grand_total", "net_total", "total_qty"],
    )

    grand_total = sum(inv.grand_total for inv in invoices)
    net_total = sum(inv.net_total for inv in invoices)
    total_qty = sum(inv.total_qty for inv in invoices)

    invoice_names = [inv.name for inv in invoices]
    payment_totals = {}

    if invoice_names:
        payments = frappe.db.sql(
            """
            SELECT mode_of_payment, SUM(amount) as total_amount
            FROM `tabSales Invoice Payment`
            WHERE parent IN %(invoices)s
            GROUP BY mode_of_payment
            """,
            {"invoices": invoice_names},
            as_dict=True,
        )
        for p in payments:
            payment_totals[p.mode_of_payment] = p.total_amount or 0

    payment_summary = []
    for bd in opening.balance_details:
        mode = bd.mode_of_payment
        opening_amount = bd.opening_amount or 0
        sales_amount = payment_totals.pop(mode, 0)
        expected = opening_amount + sales_amount

        payment_summary.append(
            {
                "mode_of_payment": mode,
                "opening_amount": opening_amount,
                "sales_amount": sales_amount,
                "expected_amount": expected,
            }
        )

    for mode, amount in payment_totals.items():
        payment_summary.append(
            {
                "mode_of_payment": mode,
                "opening_amount": 0,
                "sales_amount": amount,
                "expected_amount": amount,
            }
        )

    return {
        "invoices": invoices,
        "grand_total": grand_total,
        "net_total": net_total,
        "total_quantity": total_qty,
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
    """Get full POS Profile document."""
    doc = frappe.get_doc("POS Profile", pos_profile)
    return doc.as_dict()


@frappe.whitelist()
def close_shift(opening_entry, closing_amounts=None):
    """Create a POS Closing Entry with proper per-mode reconciliation."""
    if isinstance(closing_amounts, str):
        closing_amounts = json.loads(closing_amounts)

    # Validate opening entry exists and is open
    if not frappe.db.exists("POS Opening Entry", opening_entry):
        frappe.throw(_("Opening entry {0} does not exist").format(opening_entry))

    opening = frappe.get_doc("POS Opening Entry", opening_entry)

    if opening.status != "Open" or opening.docstatus != 1:
        frappe.throw(_("Opening entry {0} is not open or not submitted").format(opening_entry))

    # Fetch fresh summary data INSIDE the function to avoid race condition
    shift_data = _get_shift_data(opening)

    closing = frappe.get_doc(
        {
            "doctype": "POS Closing Entry",
            "user": frappe.session.user,
            "pos_profile": opening.pos_profile,
            "company": opening.company,
            "pos_opening_entry": opening_entry,
            "period_start_date": opening.period_start_date,
            "period_end_date": nowdate() + " " + nowtime(),
            "posting_date": nowdate(),
            "posting_time": nowtime(),
            "grand_total": shift_data["grand_total"],
            "net_total": shift_data["net_total"],
            "total_quantity": shift_data["total_quantity"],
        }
    )

    # Add POS transactions
    for inv in shift_data["invoices"]:
        closing.append(
            "pos_transactions",
            {
                "pos_invoice": inv.name,
                "grand_total": inv.grand_total,
            },
        )

    # Build closing amounts lookup
    closing_lookup = {}
    if closing_amounts:
        for ca in closing_amounts:
            closing_lookup[ca.get("mode_of_payment")] = ca.get("closing_amount", 0)

    # Add payment reconciliation using actual per-mode data
    for ps in shift_data["payment_summary"]:
        mode = ps["mode_of_payment"]
        closing_amount = closing_lookup.get(mode, 0)

        closing.append(
            "payment_reconciliation",
            {
                "mode_of_payment": mode,
                "opening_amount": ps["opening_amount"],
                "expected_amount": ps["expected_amount"],
                "closing_amount": closing_amount,
                "difference": closing_amount - ps["expected_amount"],
            },
        )

    closing.insert(ignore_permissions=True)
    closing.submit()

    return {"name": closing.name, "status": "Closed"}
