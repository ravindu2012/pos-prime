# Copyright (c) 2026, Ravindu Gajanayaka
# Licensed under GPLv3. See license.txt

import frappe
from frappe import _
import json

from pos_prime.api._utils import safe_float


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
            # ERPNext's coupon_code field is a Link to Coupon Code doctype (expects
            # document name, e.g. "Save 20 Percent").  The frontend sends the
            # user-facing code (e.g. "SAVE20").  Resolve to the document name.
            coupon_name = frappe.db.get_value(
                "Coupon Code", {"coupon_code": coupon_code}, "name"
            )
            invoice.coupon_code = coupon_name or coupon_code

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

        # Apply item-level Price discount rules.  set_missing_values()
        # evaluates pricing rules internally but silently discards Price
        # discount results when item fields already carry default values
        # (0 instead of None).  Product discount rules (free items) ARE
        # applied correctly by set_missing_values(), so we only handle
        # Price discounts here.
        if not profile.ignore_pricing_rule:
            from erpnext.accounts.doctype.pricing_rule.utils import (
                get_pricing_rules,
            )

            coupon_pricing_rule = None
            if coupon_code and invoice.coupon_code:
                coupon_pricing_rule = frappe.db.get_value(
                    "Coupon Code", invoice.coupon_code, "pricing_rule"
                )

            original_count = len(invoice.items)
            for idx in range(original_count):
                item = invoice.items[idx]
                if getattr(item, "is_free_item", 0):
                    continue

                item_args = frappe._dict({
                    "doctype": "POS Invoice",
                    "child_doctype": "POS Invoice Item",
                    "item_code": item.item_code,
                    "item_group": item.item_group,
                    "brand": item.brand or "",
                    "qty": item.qty,
                    "stock_qty": getattr(item, "stock_qty", None) or item.qty,
                    "rate": item.rate,
                    "price_list_rate": item.price_list_rate or item.rate,
                    "amount": item.qty * item.rate,
                    "customer": invoice.customer,
                    "customer_group": invoice.customer_group,
                    "territory": invoice.territory,
                    "company": invoice.company,
                    "transaction_type": "selling",
                    "selling": 1,
                    "price_list": invoice.selling_price_list,
                    "transaction_date": (
                        getattr(invoice, "transaction_date", None)
                        or getattr(invoice, "posting_date", None)
                        or frappe.utils.today()
                    ),
                    "coupon_code": invoice.coupon_code if coupon_code else None,
                })

                all_rules = get_pricing_rules(item_args)
                if not all_rules:
                    continue

                # Separate Price vs Product discount rules
                price_rules = []
                product_rules = []
                for rule in all_rules:
                    if not coupon_code and rule.coupon_code_based:
                        continue
                    if rule.min_qty and item.qty < rule.min_qty:
                        continue
                    if rule.min_amt and (item.qty * item.rate) < rule.min_amt:
                        continue
                    if rule.price_or_product_discount == "Product":
                        product_rules.append(rule)
                    else:
                        price_rules.append(rule)

                # --- Best Price discount ---
                best = None
                if coupon_code and coupon_pricing_rule:
                    for rule in price_rules:
                        if rule.name == coupon_pricing_rule:
                            best = rule
                            break
                if not best:
                    candidates = [r for r in price_rules if not r.coupon_code_based]
                    if candidates:
                        candidates.sort(key=lambda x: x.priority or 0, reverse=True)
                        best = candidates[0]

                if best:
                    if not item.price_list_rate:
                        item.price_list_rate = item.rate
                    item.pricing_rules = json.dumps([best.name])
                    if best.rate_or_discount == "Discount Percentage" and best.discount_percentage:
                        item.discount_percentage = best.discount_percentage
                    elif best.rate_or_discount == "Discount Amount" and best.discount_amount:
                        item.discount_amount = best.discount_amount
                    elif best.rate_or_discount == "Rate" and best.rate:
                        item.price_list_rate = best.rate
                        item.rate = best.rate
                    if best.margin_type:
                        item.margin_type = best.margin_type
                        item.margin_rate_or_amount = best.margin_rate_or_amount or 0

                # --- Best Product discount (free item) with dedup ---
                # set_missing_values() may have already added free items
                # (v15/v16), so check before adding to avoid duplicates.
                best_product = None
                if coupon_code and coupon_pricing_rule:
                    for rule in product_rules:
                        if rule.name == coupon_pricing_rule:
                            best_product = rule
                            break
                if not best_product:
                    candidates = [r for r in product_rules if not r.coupon_code_based]
                    if candidates:
                        candidates.sort(key=lambda x: x.priority or 0, reverse=True)
                        best_product = candidates[0]

                if best_product:
                    free_item_code = best_product.free_item or (
                        item.item_code if best_product.same_item else None
                    )
                    if free_item_code:
                        # Check if this free item was already added
                        already = False
                        for it in invoice.items:
                            if getattr(it, "is_free_item", 0):
                                it_pr = getattr(it, "pricing_rules", "") or ""
                                if best_product.name in it_pr:
                                    already = True
                                    break
                        if not already:
                            invoice.append("items", {
                                "item_code": free_item_code,
                                "qty": best_product.free_qty or 1,
                                "rate": best_product.free_item_rate or 0,
                                "is_free_item": 1,
                                "pricing_rules": json.dumps([best_product.name]),
                                "warehouse": profile.warehouse,
                                "income_account": profile.income_account,
                                "cost_center": profile.cost_center,
                            })

            # Coupon-based Product discount safety net.
            # get_pricing_rules() may not return coupon_code_based rules on
            # all ERPNext versions.  Directly check and add if missing.
            if coupon_code and coupon_pricing_rule:
                pr_type = frappe.db.get_value(
                    "Pricing Rule", coupon_pricing_rule, "price_or_product_discount"
                )
                if pr_type == "Product":
                    already_added = any(
                        coupon_pricing_rule in (getattr(it, "pricing_rules", "") or "")
                        for it in invoice.items
                        if getattr(it, "is_free_item", 0)
                    )
                    if not already_added:
                        pr_doc = frappe.get_doc("Pricing Rule", coupon_pricing_rule)
                        if pr_doc.free_item:
                            invoice.append("items", {
                                "item_code": pr_doc.free_item,
                                "qty": pr_doc.free_qty or 1,
                                "rate": pr_doc.free_item_rate or 0,
                                "is_free_item": 1,
                                "pricing_rules": json.dumps([coupon_pricing_rule]),
                                "warehouse": profile.warehouse,
                                "income_account": profile.income_account,
                                "cost_center": profile.cost_center,
                            })

        invoice.calculate_taxes_and_totals()

        # Apply transaction-level pricing rules (e.g. "Apply On: Transaction")
        if not profile.ignore_pricing_rule:
            from erpnext.accounts.doctype.pricing_rule.utils import (
                apply_pricing_rule_on_transaction,
            )

            apply_pricing_rule_on_transaction(invoice)

            # ERPNext bug: apply_pricing_rule_on_transaction doesn't check
            # coupon_code_based for product discounts (free items). Remove
            # free items added by coupon-code-based rules when no coupon is provided.
            if not coupon_code:
                to_remove = []
                for item in invoice.items:
                    if getattr(item, "is_free_item", 0) and getattr(item, "pricing_rules", None):
                        pr_name = item.pricing_rules.strip('"')
                        if frappe.db.get_value("Pricing Rule", pr_name, "coupon_code_based"):
                            to_remove.append(item)
                for item in to_remove:
                    invoice.remove(item)
                if to_remove:
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

        # Extract pricing rule data from items
        pricing_rules = []
        free_items = []
        for item in invoice.items:
            pr = getattr(item, "pricing_rules", None)
            is_free = getattr(item, "is_free_item", 0)
            if is_free:
                free_items.append({
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "qty": item.qty,
                    "rate": item.rate,
                    "amount": item.amount,
                    "uom": item.uom or item.stock_uom,
                    "stock_uom": item.stock_uom,
                    "pricing_rules": pr or "",
                    "is_free_item": 1,
                })
            elif pr and pr not in ("[]", "[\n]", "null", ""):
                pricing_rules.append({
                    "item_code": item.item_code,
                    "pricing_rules": pr,
                    "rate": item.rate,
                    "price_list_rate": item.price_list_rate,
                    "discount_percentage": item.discount_percentage or 0,
                    "discount_amount": item.discount_amount or 0,
                    "margin_type": item.margin_type or "",
                    "margin_rate_or_amount": item.margin_rate_or_amount or 0,
                    "rate_with_margin": item.rate_with_margin or 0,
                })

        return {
            "net_total": invoice.net_total,
            "taxes": taxes,
            "total_taxes_and_charges": invoice.total_taxes_and_charges,
            "grand_total": invoice.grand_total,
            "rounded_total": invoice.rounded_total,
            "rounding_adjustment": invoice.rounding_adjustment,
            "discount_amount": invoice.discount_amount,
            "additional_discount_percentage": invoice.additional_discount_percentage,
            "apply_discount_on": invoice.apply_discount_on,
            "pricing_rules": pricing_rules,
            "free_items": free_items,
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "POS Prime: calculate_taxes failed")
        frappe.throw(_("Failed to calculate taxes: {0}").format(str(e)))


@frappe.whitelist()
def validate_coupon_code(coupon_code, customer=None):
    """Validate a coupon code and return its details if valid.

    Matches against the `coupon_code` field (the code the user enters),
    not the document `name` (which is based on `coupon_name`).
    """
    if not coupon_code:
        frappe.throw(_("Coupon code is required"))

    coupon = frappe.db.get_value(
        "Coupon Code",
        {"coupon_code": coupon_code},
        [
            "name",
            "coupon_name",
            "coupon_code",
            "coupon_type",
            "pricing_rule",
            "valid_from",
            "valid_upto",
            "used",
            "maximum_use",
            "customer",
        ],
        as_dict=True,
    )

    if not coupon:
        frappe.throw(_("Invalid coupon code"))

    today = frappe.utils.today()
    if coupon.valid_from and frappe.utils.getdate(coupon.valid_from) > frappe.utils.getdate(today):
        frappe.throw(_("Coupon code is not yet valid"))

    if coupon.valid_upto and frappe.utils.getdate(coupon.valid_upto) < frappe.utils.getdate(today):
        frappe.throw(_("Coupon code has expired"))

    if coupon.maximum_use and coupon.used >= coupon.maximum_use:
        frappe.throw(_("Coupon code usage limit exceeded"))

    if coupon.customer and customer and coupon.customer != customer:
        frappe.throw(_("This coupon is not valid for the selected customer"))

    # Check that the linked pricing rule exists and is active
    if coupon.pricing_rule:
        pr_disabled = frappe.db.get_value("Pricing Rule", coupon.pricing_rule, "disable")
        if pr_disabled:
            frappe.throw(_("The pricing rule linked to this coupon is disabled"))

    return {
        "name": coupon.name,
        "coupon_code": coupon.coupon_code,
        "coupon_name": coupon.coupon_name,
        "coupon_type": coupon.coupon_type,
        "pricing_rule": coupon.pricing_rule,
    }
