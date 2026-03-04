import frappe
from frappe import _
import json

from posify.api._utils import safe_float


@frappe.whitelist()
def calculate_taxes(
    pos_profile,
    customer,
    items,
    additional_discount_percentage=0,
    discount_amount=0,
    apply_discount_on="Grand Total",
    coupon_code=None,
):
    """Calculate taxes using ERPNext's built-in tax engine.

    Creates a temporary POS Invoice in memory, sets missing values,
    and runs calculate_taxes_and_totals() without saving.
    """
    try:
        if isinstance(items, str):
            items = json.loads(items)

        profile = frappe.get_doc("POS Profile", pos_profile)

        invoice = frappe.get_doc(
            {
                "doctype": "POS Invoice",
                "customer": customer,
                "company": profile.company,
                "pos_profile": pos_profile,
                "is_pos": 1,
                "selling_price_list": profile.selling_price_list or "Standard Selling",
                "currency": profile.currency
                or frappe.defaults.get_defaults().get("currency", "USD"),
                "set_warehouse": profile.warehouse,
                "update_stock": 0,  # Don't affect stock for calculation
                "taxes_and_charges": profile.taxes_and_charges or "",
                "apply_discount_on": apply_discount_on,
                "ignore_pricing_rule": 1 if profile.ignore_pricing_rule else 0,
            }
        )

        if additional_discount_percentage:
            invoice.additional_discount_percentage = safe_float(additional_discount_percentage)

        if discount_amount:
            invoice.discount_amount = safe_float(discount_amount)

        if coupon_code:
            invoice.coupon_code = coupon_code

        # Tax category from profile
        if profile.tax_category:
            invoice.tax_category = profile.tax_category

        # Add items with full field support
        for item_data in items:
            item_dict = {
                "item_code": item_data.get("item_code"),
                "qty": item_data.get("qty", 1),
                "rate": item_data.get("rate", 0),
                "discount_percentage": item_data.get("discount_percentage", 0),
                "warehouse": profile.warehouse,
                "income_account": profile.income_account,
                "cost_center": profile.cost_center,
                "serial_no": item_data.get("serial_no", ""),
                "batch_no": item_data.get("batch_no", ""),
                "uom": item_data.get("uom", ""),
                "conversion_factor": item_data.get("conversion_factor", 1),
            }
            # Flat discount amount
            if item_data.get("discount_amount"):
                item_dict["discount_amount"] = item_data["discount_amount"]
            # Item tax template
            if item_data.get("item_tax_template"):
                item_dict["item_tax_template"] = item_data["item_tax_template"]
            # Margin
            if item_data.get("margin_type"):
                item_dict["margin_type"] = item_data["margin_type"]
                item_dict["margin_rate_or_amount"] = item_data.get("margin_rate_or_amount", 0)
            invoice.append("items", item_dict)

        # Use ERPNext's built-in tax calculation
        invoice.set_missing_values()
        invoice.calculate_taxes_and_totals()

        # Build tax rows
        taxes = []
        for tax in invoice.taxes:
            taxes.append(
                {
                    "charge_type": tax.charge_type,
                    "account_head": tax.account_head,
                    "description": tax.description,
                    "rate": tax.rate,
                    "tax_amount": tax.tax_amount,
                    "total": tax.total,
                }
            )

        return {
            "net_total": invoice.net_total,
            "taxes": taxes,
            "total_taxes_and_charges": invoice.total_taxes_and_charges,
            "grand_total": invoice.grand_total,
            "rounded_total": invoice.rounded_total,
            "rounding_adjustment": invoice.rounding_adjustment,
            "discount_amount": invoice.discount_amount,
            "additional_discount_percentage": invoice.additional_discount_percentage,
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Posify: calculate_taxes failed")
        frappe.throw(_("Failed to calculate taxes: {0}").format(str(e)))
