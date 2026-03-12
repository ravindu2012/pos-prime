# Copyright (c) 2026, Ravindu Gajanayaka
# Licensed under GPLv3. See license.txt

"""Shared utility functions for POS Prime API endpoints."""

import frappe


def validate_pos_access(pos_profile=None):
    """Validate that the current user has POS access.

    Checks:
    1. User has read permission on POS Invoice (respects Role Permissions Manager,
       including custom roles like "POS Operator", "Cashier", etc.).
    2. If pos_profile is provided, user is in the profile's applicable_for_users
       (or the list is empty, meaning all users are allowed).

    Raises frappe.PermissionError if not authorized.
    """
    if not frappe.has_permission("POS Invoice", "read"):
        frappe.throw(
            "You do not have permission to access POS. "
            "Please contact your administrator to grant POS Invoice access.",
            frappe.PermissionError,
        )

    if pos_profile:
        if not frappe.db.exists("POS Profile", pos_profile):
            frappe.throw(
                f"POS Profile '{pos_profile}' does not exist.",
                frappe.DoesNotExistError,
            )
        profile = frappe.get_doc("POS Profile", pos_profile)
        if profile.get("applicable_for_users") and len(profile.applicable_for_users) > 0:
            allowed_users = [u.user for u in profile.applicable_for_users]
            if frappe.session.user not in allowed_users:
                frappe.throw(
                    "You are not allowed to use this POS Profile.",
                    frappe.PermissionError,
                )


def safe_float(value, default=0):
    """Safely convert a value to float, returning default on failure."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def build_item_dict(item_data, profile):
    """Build a POS Invoice Item dict from request data and POS Profile.

    Supports all POS Invoice Item fields including discount_amount,
    item_tax_template, margin, description, project, etc.
    """
    item_dict = {
        "item_code": item_data.get("item_code"),
        "qty": item_data.get("qty", 1),
        "rate": item_data.get("rate", 0),
        "discount_percentage": item_data.get("discount_percentage", 0),
        "warehouse": item_data.get("warehouse") or profile.warehouse,
        "income_account": item_data.get("income_account") or profile.income_account,
        "cost_center": item_data.get("cost_center") or profile.cost_center,
    }

    # Flat discount amount (alternative to percentage)
    if item_data.get("discount_amount"):
        item_dict["discount_amount"] = item_data["discount_amount"]

    # Item tax template
    if item_data.get("item_tax_template"):
        item_dict["item_tax_template"] = item_data["item_tax_template"]

    # Margin
    if item_data.get("margin_type"):
        item_dict["margin_type"] = item_data["margin_type"]
        item_dict["margin_rate_or_amount"] = item_data.get("margin_rate_or_amount", 0)

    # Serial/batch
    if item_data.get("serial_no"):
        item_dict["serial_no"] = item_data["serial_no"]
    if item_data.get("batch_no"):
        item_dict["batch_no"] = item_data["batch_no"]
    # serial_and_batch_bundle only exists in v15+ (not in v14)
    if item_data.get("serial_and_batch_bundle"):
        if frappe.get_meta("POS Invoice Item").has_field("serial_and_batch_bundle"):
            item_dict["serial_and_batch_bundle"] = item_data["serial_and_batch_bundle"]
    if item_data.get("use_serial_batch_fields") is not None:
        if frappe.get_meta("POS Invoice Item").has_field("use_serial_batch_fields"):
            item_dict["use_serial_batch_fields"] = item_data["use_serial_batch_fields"]

    # UOM
    if item_data.get("uom"):
        item_dict["uom"] = item_data["uom"]
    if item_data.get("conversion_factor"):
        item_dict["conversion_factor"] = item_data["conversion_factor"]

    # Description
    if item_data.get("description"):
        item_dict["description"] = item_data["description"]

    # Project (item-level)
    if item_data.get("project"):
        item_dict["project"] = item_data["project"]

    # Expense account (with profile fallback)
    expense_account = item_data.get("expense_account") or getattr(profile, "expense_account", None)
    if expense_account:
        item_dict["expense_account"] = expense_account

    # Weight
    if item_data.get("weight_per_unit"):
        item_dict["weight_per_unit"] = item_data["weight_per_unit"]
    if item_data.get("weight_uom"):
        item_dict["weight_uom"] = item_data["weight_uom"]

    return item_dict


def set_invoice_optional_fields(invoice, profile, **kwargs):
    """Set optional fields on a POS Invoice doc from keyword arguments.

    Only sets fields that are provided (non-None). Falls back to POS Profile
    values where appropriate.
    """
    # Address & contact
    if kwargs.get("customer_address"):
        invoice.customer_address = kwargs["customer_address"]
    if kwargs.get("shipping_address_name"):
        invoice.shipping_address_name = kwargs["shipping_address_name"]
    if kwargs.get("contact_person"):
        invoice.contact_person = kwargs["contact_person"]

    # Currency conversion
    if kwargs.get("conversion_rate"):
        invoice.conversion_rate = safe_float(kwargs["conversion_rate"])
    if kwargs.get("price_list_currency"):
        invoice.price_list_currency = kwargs["price_list_currency"]
    if kwargs.get("plc_conversion_rate"):
        invoice.plc_conversion_rate = safe_float(kwargs["plc_conversion_rate"])

    # Commission
    if kwargs.get("sales_partner"):
        invoice.sales_partner = kwargs["sales_partner"]
    if kwargs.get("commission_rate") is not None and kwargs.get("sales_partner"):
        invoice.commission_rate = safe_float(kwargs["commission_rate"])

    # Document details
    project = kwargs.get("project") or getattr(profile, "project", None)
    if project:
        invoice.project = project
    if kwargs.get("cost_center"):
        invoice.cost_center = kwargs["cost_center"]
    if kwargs.get("remarks"):
        invoice.remarks = kwargs["remarks"]
    if kwargs.get("po_no"):
        invoice.po_no = kwargs["po_no"]
    if kwargs.get("po_date"):
        invoice.po_date = kwargs["po_date"]

    # Posting date/time override
    if kwargs.get("set_posting_time"):
        invoice.set_posting_time = 1
        if kwargs.get("posting_date"):
            invoice.posting_date = kwargs["posting_date"]
        if kwargs.get("posting_time"):
            invoice.posting_time = kwargs["posting_time"]

    # Naming series
    if kwargs.get("naming_series"):
        invoice.naming_series = kwargs["naming_series"]

    # Shipping & terms
    if kwargs.get("shipping_rule"):
        invoice.shipping_rule = kwargs["shipping_rule"]
    tc = kwargs.get("tc_name") or getattr(profile, "tc_name", None)
    if tc:
        invoice.tc_name = tc
    if kwargs.get("terms"):
        invoice.terms = kwargs["terms"]

    # Printing
    lh = kwargs.get("letter_head") or getattr(profile, "letter_head", None)
    if lh:
        invoice.letter_head = lh
    ph = kwargs.get("select_print_heading") or getattr(profile, "select_print_heading", None)
    if ph:
        invoice.select_print_heading = ph
    if kwargs.get("group_same_items"):
        invoice.group_same_items = 1
    if kwargs.get("language"):
        invoice.language = kwargs["language"]

    # Payment terms & advances
    if kwargs.get("payment_terms_template"):
        invoice.payment_terms_template = kwargs["payment_terms_template"]
    if kwargs.get("allocate_advances_automatically"):
        invoice.allocate_advances_automatically = 1

    # Write-off
    if kwargs.get("write_off_amount"):
        invoice.write_off_amount = safe_float(kwargs["write_off_amount"])
    if kwargs.get("write_off_outstanding_amount_automatically"):
        invoice.write_off_outstanding_amount_automatically = 1

    # Debit account
    if kwargs.get("debit_to"):
        invoice.debit_to = kwargs["debit_to"]

    # Sales team
    if kwargs.get("sales_team"):
        for member in kwargs["sales_team"]:
            invoice.append("sales_team", member)


def set_campaign_from_profile(invoice, profile):
    """Set campaign field on invoice from POS Profile, handling v14/v15/v16 field rename."""
    # v16 renamed 'campaign' to 'utm_campaign' on both POS Profile and POS Invoice
    for field_name in ("utm_campaign", "campaign"):
        value = profile.get(field_name)
        if value:
            if frappe.get_meta("POS Invoice").has_field(field_name):
                setattr(invoice, field_name, value)
            break


def get_product_bundle_items(item_code):
    """Get component items for a Product Bundle. Returns [] if not a bundle."""
    if not frappe.db.exists("Product Bundle", {"new_item_code": item_code, "disabled": 0}):
        return []
    return frappe.get_all(
        "Product Bundle Item",
        filters={"parent": item_code, "parenttype": "Product Bundle"},
        fields=["item_code", "qty", "description"],
        order_by="idx asc",
    )


def validate_bundle_stock(item_code, qty, warehouse):
    """Validate that all components of a Product Bundle have sufficient stock.

    Raises frappe.ValidationError if any component has insufficient stock.
    """
    components = get_product_bundle_items(item_code)
    if not components:
        return  # Not a bundle, nothing to validate

    # Batch fetch actual_qty for all components in one query
    comp_codes = [c.item_code for c in components]
    bin_data = {
        r.item_code: r.actual_qty
        for r in frappe.get_all(
            "Bin",
            filters={"item_code": ["in", comp_codes], "warehouse": warehouse},
            fields=["item_code", "actual_qty"],
        )
    }

    for comp in components:
        required_qty = comp.qty * qty
        actual_qty = bin_data.get(comp.item_code, 0) or 0
        if required_qty > actual_qty:
            frappe.throw(
                "Product Bundle {0}: Component {1} has insufficient stock. "
                "Available: {2}, Required: {3}".format(
                    item_code, comp.item_code, actual_qty, required_qty
                )
            )


def get_bundle_availability(item_code, warehouse):
    """Calculate how many complete bundles can be fulfilled from component stock."""
    components = get_product_bundle_items(item_code)
    if not components:
        return 0

    comp_codes = [c.item_code for c in components if c.qty > 0]
    if not comp_codes:
        return 0

    # Batch fetch is_stock_item for all components in one query
    stock_items = {
        r.name
        for r in frappe.get_all(
            "Item",
            filters={"name": ["in", comp_codes], "is_stock_item": 1},
            fields=["name"],
        )
    }

    # Batch fetch actual_qty for all stock components in one query
    bin_data = {
        r.item_code: r.actual_qty
        for r in frappe.get_all(
            "Bin",
            filters={"item_code": ["in", list(stock_items)], "warehouse": warehouse},
            fields=["item_code", "actual_qty"],
        )
    } if stock_items else {}

    min_bundles = float("inf")
    for comp in components:
        if comp.qty <= 0:
            continue
        if comp.item_code not in stock_items:
            continue
        actual_qty = bin_data.get(comp.item_code, 0) or 0
        possible = actual_qty // comp.qty
        min_bundles = min(min_bundles, possible)

    return int(min_bundles) if min_bundles != float("inf") else 0


def format_invoice_response(invoice):
    """Format a POS Invoice doc into a comprehensive API response dict.

    Returns ALL relevant POS Invoice fields so the frontend has complete data.
    """
    return {
        # Identity
        "name": invoice.name,
        "naming_series": invoice.get("naming_series"),
        "status": invoice.status,
        "docstatus": invoice.docstatus,
        "owner": invoice.owner,
        "modified": str(invoice.modified) if invoice.modified else None,

        # Customer
        "customer": invoice.customer,
        "customer_name": invoice.customer_name,
        "tax_id": invoice.get("tax_id"),

        # Address & contact
        "customer_address": invoice.get("customer_address"),
        "address_display": invoice.get("address_display"),
        "contact_person": invoice.get("contact_person"),
        "contact_display": invoice.get("contact_display"),
        "contact_mobile": invoice.get("contact_mobile"),
        "contact_email": invoice.get("contact_email"),
        "territory": invoice.get("territory"),
        "shipping_address_name": invoice.get("shipping_address_name"),
        "shipping_address": invoice.get("shipping_address"),
        "company_address": invoice.get("company_address"),
        "company_address_display": invoice.get("company_address_display"),

        # Company & configuration
        "company": invoice.company,
        "pos_profile": invoice.pos_profile,
        "posting_date": str(invoice.posting_date),
        "posting_time": str(invoice.posting_time),
        "set_posting_time": invoice.get("set_posting_time"),
        "due_date": str(invoice.due_date) if invoice.get("due_date") else None,

        # Currency
        "currency": invoice.currency,
        "conversion_rate": invoice.get("conversion_rate"),
        "selling_price_list": invoice.get("selling_price_list"),
        "price_list_currency": invoice.get("price_list_currency"),
        "plc_conversion_rate": invoice.get("plc_conversion_rate"),

        # Totals
        "total_qty": invoice.get("total_qty"),
        "total": invoice.get("total"),
        "net_total": invoice.net_total,
        "grand_total": invoice.grand_total,
        "rounded_total": invoice.get("rounded_total"),
        "rounding_adjustment": invoice.get("rounding_adjustment"),
        "in_words": invoice.get("in_words"),

        # Base currency totals
        "base_total": invoice.get("base_total"),
        "base_net_total": invoice.get("base_net_total"),
        "base_grand_total": invoice.get("base_grand_total"),
        "base_rounded_total": invoice.get("base_rounded_total"),
        "base_rounding_adjustment": invoice.get("base_rounding_adjustment"),
        "base_in_words": invoice.get("base_in_words"),

        # Payment
        "paid_amount": invoice.paid_amount,
        "base_paid_amount": invoice.get("base_paid_amount"),
        "change_amount": invoice.change_amount,
        "base_change_amount": invoice.get("base_change_amount"),
        "outstanding_amount": invoice.get("outstanding_amount"),
        "total_advance": invoice.get("total_advance"),
        "account_for_change_amount": invoice.get("account_for_change_amount"),

        # Taxes
        "taxes_and_charges": invoice.get("taxes_and_charges"),
        "tax_category": invoice.get("tax_category"),
        "shipping_rule": invoice.get("shipping_rule"),
        "total_taxes_and_charges": invoice.get("total_taxes_and_charges"),
        "base_total_taxes_and_charges": invoice.get("base_total_taxes_and_charges"),

        # Discount
        "apply_discount_on": invoice.get("apply_discount_on"),
        "additional_discount_percentage": invoice.get("additional_discount_percentage"),
        "discount_amount": invoice.get("discount_amount"),
        "base_discount_amount": invoice.get("base_discount_amount"),
        "coupon_code": invoice.get("coupon_code"),

        # Loyalty
        "loyalty_points": invoice.get("loyalty_points"),
        "loyalty_amount": invoice.get("loyalty_amount"),
        "redeem_loyalty_points": invoice.get("redeem_loyalty_points"),
        "loyalty_program": invoice.get("loyalty_program"),
        "loyalty_redemption_account": invoice.get("loyalty_redemption_account"),
        "loyalty_redemption_cost_center": invoice.get("loyalty_redemption_cost_center"),

        # Return
        "is_return": invoice.is_return,
        "return_against": invoice.return_against,

        # Write-off
        "write_off_amount": invoice.get("write_off_amount"),
        "base_write_off_amount": invoice.get("base_write_off_amount"),
        "write_off_account": invoice.get("write_off_account"),
        "write_off_cost_center": invoice.get("write_off_cost_center"),

        # Commission
        "sales_partner": invoice.get("sales_partner"),
        "commission_rate": invoice.get("commission_rate"),
        "total_commission": invoice.get("total_commission"),

        # Document details
        "project": invoice.get("project"),
        "cost_center": invoice.get("cost_center"),
        "po_no": invoice.get("po_no"),
        "po_date": str(invoice.po_date) if invoice.get("po_date") else None,
        "remarks": invoice.get("remarks"),
        "campaign": invoice.get("campaign") or invoice.get("utm_campaign"),

        # Printing
        "letter_head": invoice.get("letter_head"),
        "select_print_heading": invoice.get("select_print_heading"),
        "group_same_items": invoice.get("group_same_items"),
        "language": invoice.get("language"),
        "print_format": invoice.get("print_format"),

        # Payment terms
        "payment_terms_template": invoice.get("payment_terms_template"),
        "allocate_advances_automatically": invoice.get("allocate_advances_automatically"),

        # Consolidated
        "consolidated_invoice": invoice.get("consolidated_invoice"),
        "is_discounted": invoice.get("is_discounted"),

        # Weight
        "total_net_weight": invoice.get("total_net_weight"),

        # Child tables
        "items": [format_invoice_item(item) for item in invoice.items],
        "payments": [
            {"mode_of_payment": p.mode_of_payment, "amount": p.amount}
            for p in invoice.payments
        ],
        "taxes": [
            {
                "charge_type": tax.charge_type,
                "account_head": tax.account_head,
                "description": tax.description,
                "rate": tax.rate,
                "tax_amount": tax.tax_amount,
                "total": tax.total,
                "base_tax_amount": tax.get("base_tax_amount"),
                "base_total": tax.get("base_total"),
            }
            for tax in invoice.taxes
        ],
    }


def format_invoice_item(item):
    """Format a single POS Invoice Item for API response."""
    return {
        "item_code": item.item_code,
        "item_name": item.item_name,
        "description": item.get("description"),
        "item_group": item.get("item_group"),
        "brand": item.get("brand"),
        "qty": item.qty,
        "stock_qty": item.get("stock_qty"),
        "rate": item.rate,
        "amount": item.amount,
        "price_list_rate": item.get("price_list_rate"),
        "base_rate": item.get("base_rate"),
        "base_amount": item.get("base_amount"),
        "net_rate": item.get("net_rate"),
        "net_amount": item.get("net_amount"),
        "uom": item.uom,
        "stock_uom": item.get("stock_uom"),
        "conversion_factor": item.get("conversion_factor"),
        "discount_percentage": item.discount_percentage,
        "discount_amount": item.get("discount_amount"),
        "margin_type": item.get("margin_type"),
        "margin_rate_or_amount": item.get("margin_rate_or_amount"),
        "rate_with_margin": item.get("rate_with_margin"),
        "item_tax_template": item.get("item_tax_template"),
        "item_tax_rate": item.get("item_tax_rate"),
        "is_free_item": item.get("is_free_item"),
        "serial_no": item.serial_no,
        "batch_no": item.batch_no,
        "serial_and_batch_bundle": item.get("serial_and_batch_bundle") if frappe.get_meta("POS Invoice Item").has_field("serial_and_batch_bundle") else None,
        "actual_qty": item.get("actual_qty"),
        "warehouse": item.get("warehouse"),
        "income_account": item.get("income_account"),
        "expense_account": item.get("expense_account"),
        "cost_center": item.get("cost_center"),
        "project": item.get("project"),
        "weight_per_unit": item.get("weight_per_unit"),
        "total_weight": item.get("total_weight"),
        "weight_uom": item.get("weight_uom"),
    }
