import frappe
from frappe import _
import json

from posify.api._utils import (
    build_item_dict,
    format_invoice_response,
    validate_pos_access,
    safe_float,
)


@frappe.whitelist()
def get_past_orders(pos_profile, search_term="", status="", limit=20, start=0):
    """Get paginated list of past POS Invoices with search/filter."""
    validate_pos_access(pos_profile)

    try:
        filters = {
            "pos_profile": pos_profile,
        }

        if status == "Paid":
            filters["docstatus"] = 1
            filters["is_return"] = 0
        elif status == "Return":
            filters["docstatus"] = 1
            filters["is_return"] = 1
        elif status == "Draft":
            filters["docstatus"] = 0
        elif status == "Consolidated":
            filters["docstatus"] = 1
            filters["status"] = "Consolidated"
        else:
            # All -- no extra filter
            pass

        or_filters = {}
        if search_term:
            search = f"%{search_term}%"
            or_filters = {
                "name": ["like", search],
                "customer_name": ["like", search],
                "customer": ["like", search],
            }

        orders = frappe.get_list(
            "POS Invoice",
            filters=filters,
            or_filters=or_filters if or_filters else None,
            fields=[
                "name",
                "customer",
                "customer_name",
                "grand_total",
                "net_total",
                "paid_amount",
                "posting_date",
                "posting_time",
                "status",
                "docstatus",
                "is_return",
                "return_against",
                "owner",
                "modified",
                "currency",
                "total_qty",
                "rounded_total",
                "change_amount",
                "outstanding_amount",
                "total_taxes_and_charges",
                "discount_amount",
                "additional_discount_percentage",
                "write_off_amount",
                "loyalty_points",
                "loyalty_amount",
                "coupon_code",
                "sales_partner",
                "po_no",
                "project",
                "remarks",
                "consolidated_invoice",
            ],
            order_by="creation desc",
            start=int(start),
            page_length=int(limit),
        )

        return orders
    except frappe.PermissionError:
        raise
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Posify: get_past_orders failed")
        frappe.throw(_("Failed to fetch past orders: {0}").format(str(e)))


@frappe.whitelist()
def get_order_detail(invoice_name):
    """Get full details of a POS Invoice with ALL fields."""
    try:
        if not frappe.has_permission("POS Invoice", "read", invoice_name):
            frappe.throw(
                _("You do not have permission to view this invoice."),
                frappe.PermissionError,
            )

        invoice = frappe.get_doc("POS Invoice", invoice_name)
        return format_invoice_response(invoice)
    except frappe.PermissionError:
        raise
    except frappe.DoesNotExistError:
        frappe.throw(_("Invoice {0} does not exist").format(invoice_name))
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Posify: get_order_detail failed")
        frappe.throw(_("Failed to fetch order detail: {0}").format(str(e)))


@frappe.whitelist()
def create_return_invoice(source_invoice):
    """Create a return POS Invoice from an existing one using ERPNext's built-in method."""
    try:
        if not frappe.db.exists("POS Invoice", source_invoice):
            frappe.throw(_("Source invoice {0} does not exist").format(source_invoice))

        source_doc = frappe.get_doc("POS Invoice", source_invoice)
        if source_doc.docstatus != 1:
            frappe.throw(_("Source invoice {0} must be submitted before creating a return").format(source_invoice))

        try:
            from erpnext.accounts.doctype.pos_invoice.pos_invoice import make_sales_return
        except ImportError:
            try:
                from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_sales_return
            except ImportError:
                make_sales_return = None

        if make_sales_return is None:
            frappe.throw(_("Return invoice creation is not supported in this ERPNext version."))

        return_doc = make_sales_return(source_invoice)
        return {
            "name": return_doc.name,
            "items": [
                {
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "qty": item.qty,  # Will be negative
                    "rate": item.rate,
                    "amount": item.amount,
                }
                for item in return_doc.items
            ],
            "grand_total": return_doc.grand_total,
        }
    except frappe.PermissionError:
        raise
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Posify: create_return_invoice failed")
        frappe.throw(_("Failed to create return invoice: {0}").format(str(e)))


@frappe.whitelist()
def submit_return_invoice(invoice_name, items, payments):
    """Adjust return items and submit."""
    try:
        if isinstance(items, str):
            items = json.loads(items)
        if isinstance(payments, str):
            payments = json.loads(payments)

        if not frappe.db.exists("POS Invoice", invoice_name):
            frappe.throw(_("Invoice {0} does not exist").format(invoice_name))

        invoice = frappe.get_doc("POS Invoice", invoice_name)

        if invoice.docstatus != 0:
            frappe.throw(_("Invoice {0} is not a draft").format(invoice_name))

        if not items:
            frappe.throw(_("Items cannot be empty for return submission"))

        # Update items with adjusted return quantities
        for i, item_data in enumerate(items):
            if i < len(invoice.items):
                invoice.items[i].qty = item_data.get("qty", invoice.items[i].qty)

        # Remove items with 0 qty
        invoice.items = [item for item in invoice.items if item.qty != 0]

        if not invoice.items:
            frappe.throw(_("At least one item with non-zero quantity is required"))

        # Set payments
        invoice.payments = []
        total_paid = 0
        for payment_data in payments:
            amount = safe_float(payment_data.get("amount", 0))
            total_paid += amount
            invoice.append(
                "payments",
                {
                    "mode_of_payment": payment_data.get("mode_of_payment"),
                    "amount": amount,
                },
            )

        invoice.paid_amount = total_paid
        invoice.base_paid_amount = total_paid

        invoice.save(ignore_permissions=True)
        invoice.submit()

        return format_invoice_response(invoice)
    except frappe.PermissionError:
        raise
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Posify: submit_return_invoice failed")
        frappe.throw(_("Failed to submit return invoice: {0}").format(str(e)))


@frappe.whitelist()
def create_manual_return(customer, pos_profile, items, mode_of_payment):
    """Create and submit a return POS Invoice from manually entered items.

    Items should have positive qty/rate — they will be negated automatically.
    """
    validate_pos_access(pos_profile)

    if isinstance(items, str):
        items = json.loads(items)

    if not items:
        frappe.throw(_("At least one item is required for a return"))

    try:
        profile = frappe.get_doc("POS Profile", pos_profile)

        invoice = frappe.get_doc({
            "doctype": "POS Invoice",
            "customer": customer,
            "company": profile.company,
            "pos_profile": pos_profile,
            "is_pos": 1,
            "is_return": 1,
            "selling_price_list": profile.selling_price_list or "Standard Selling",
            "currency": profile.currency
            or frappe.defaults.get_defaults().get("currency", "USD"),
            "set_warehouse": profile.warehouse,
            "account_for_change_amount": profile.account_for_change_amount
            or profile.write_off_account,
            "write_off_account": profile.write_off_account,
            "write_off_cost_center": profile.write_off_cost_center,
            "apply_discount_on": profile.apply_discount_on or "Grand Total",
            "ignore_pricing_rule": 1 if profile.ignore_pricing_rule else 0,
        })

        if profile.company_address:
            invoice.company_address = profile.company_address

        if profile.taxes_and_charges:
            invoice.taxes_and_charges = profile.taxes_and_charges
        if profile.tax_category:
            invoice.tax_category = profile.tax_category

        # Add items with negative qty
        for item_data in items:
            item_dict = build_item_dict(item_data, profile)
            item_dict["qty"] = -abs(safe_float(item_dict.get("qty", 1)))
            invoice.append("items", item_dict)

        # Compute return total (will be negative)
        return_total = sum(
            safe_float(i.get("qty", 1)) * safe_float(i.get("rate", 0))
            for i in items
        )

        invoice.append("payments", {
            "mode_of_payment": mode_of_payment,
            "amount": -abs(return_total),
        })
        invoice.paid_amount = -abs(return_total)
        invoice.base_paid_amount = -abs(return_total)

        invoice.flags.ignore_permissions = True
        invoice.set_missing_values()
        invoice.insert()
        invoice.submit()

        return format_invoice_response(invoice)
    except frappe.PermissionError:
        raise
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Posify: create_manual_return failed")
        frappe.throw(_("Failed to process return: {0}").format(str(e)))
