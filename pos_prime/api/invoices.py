# Copyright (c) 2026, Ravindu Gajanayaka
# Licensed under GPLv3. See license.txt

import frappe
from frappe import _
from frappe.utils import flt
import json

from pos_prime.api._utils import (
    build_item_dict,
    set_invoice_optional_fields,
    format_invoice_response,
    validate_pos_access,
    safe_float,
    get_product_bundle_items,
    validate_bundle_stock,
    set_campaign_from_profile,
)


@frappe.whitelist()
def create_pos_invoice(
    customer,
    pos_profile,
    items,
    payments,
    # Tax & discount
    taxes=None,
    additional_discount_percentage=0,
    discount_amount=0,
    apply_discount_on="Grand Total",
    coupon_code=None,
    # Loyalty
    loyalty_points=0,
    loyalty_program=None,
    redeem_loyalty_points=False,
    loyalty_redemption_account=None,
    loyalty_redemption_cost_center=None,
    # Return
    is_return=False,
    return_against=None,
    # Address & contact
    customer_address=None,
    shipping_address_name=None,
    contact_person=None,
    # Currency
    conversion_rate=None,
    price_list_currency=None,
    plc_conversion_rate=None,
    # Commission
    sales_partner=None,
    commission_rate=None,
    # Document details
    project=None,
    cost_center=None,
    remarks=None,
    po_no=None,
    po_date=None,
    set_posting_time=False,
    posting_date=None,
    posting_time=None,
    naming_series=None,
    # Shipping & terms
    shipping_rule=None,
    tc_name=None,
    terms=None,
    # Printing
    letter_head=None,
    select_print_heading=None,
    group_same_items=False,
    language=None,
    # Payment terms & advances
    payment_terms_template=None,
    allocate_advances_automatically=False,
    # Write-off
    write_off_amount=0,
    write_off_outstanding_amount_automatically=False,
    debit_to=None,
    # Store credit
    store_credit_amount=0,
    # Sales team
    sales_team=None,
):
    """Create and submit a POS Invoice with full feature support.

    Supports ALL POS Invoice fields for complete parity with ERPNext's built-in POS.
    """
    # Permission check
    validate_pos_access(pos_profile)

    if isinstance(items, str):
        items = json.loads(items)
    if isinstance(payments, str):
        payments = json.loads(payments)
    if isinstance(sales_team, str):
        sales_team = json.loads(sales_team)

    # Input validation
    if not items:
        frappe.throw(_("Items cannot be empty"))

    profile = frappe.get_doc("POS Profile", pos_profile)

    if not payments and not getattr(profile, "allow_partial_payment", 0) and not flt(store_credit_amount) and not (redeem_loyalty_points and flt(loyalty_points)):
        frappe.throw(_("Payments cannot be empty"))

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
            "update_stock": getattr(profile, "update_stock", 0),
            "account_for_change_amount": profile.account_for_change_amount
            or profile.write_off_account,
            "write_off_account": profile.write_off_account,
            "write_off_cost_center": profile.write_off_cost_center,
            "apply_discount_on": apply_discount_on or profile.apply_discount_on or "Grand Total",
            "ignore_pricing_rule": 1 if profile.ignore_pricing_rule else 0,
            "disable_rounded_total": 1 if profile.disable_rounded_total else 0,
        }
    )

    # Company address from POS Profile
    if profile.company_address:
        invoice.company_address = profile.company_address

    # Items
    for item_data in items:
        invoice.append("items", build_item_dict(item_data, profile))

    # Payments
    total_paid = 0
    for payment_data in payments:
        amount = safe_float(payment_data.get("amount", 0))
        if amount <= 0:
            continue
        total_paid += amount
        invoice.append(
            "payments",
            {
                "mode_of_payment": payment_data.get("mode_of_payment"),
                "amount": amount,
            },
        )

    # ERPNext requires at least one payment row — add a zero-amount default
    # when partial payment or store credit is used but no cash payments were provided
    if not invoice.payments:
        default_mop = profile.payments[0].mode_of_payment if profile.payments else "Cash"
        invoice.append("payments", {"mode_of_payment": default_mop, "amount": 0})

    invoice.paid_amount = total_paid

    # Taxes template
    if taxes:
        invoice.taxes_and_charges = taxes
    elif profile.taxes_and_charges:
        invoice.taxes_and_charges = profile.taxes_and_charges

    # Tax category
    if profile.tax_category:
        invoice.tax_category = profile.tax_category

    # Discounts
    if additional_discount_percentage:
        invoice.additional_discount_percentage = safe_float(additional_discount_percentage)
    if discount_amount:
        invoice.discount_amount = safe_float(discount_amount)
    if coupon_code:
        invoice.coupon_code = coupon_code

    # Loyalty
    if redeem_loyalty_points and loyalty_points:
        invoice.redeem_loyalty_points = 1
        invoice.loyalty_points = int(safe_float(loyalty_points))
        if loyalty_program:
            invoice.loyalty_program = loyalty_program
        if loyalty_redemption_account:
            invoice.loyalty_redemption_account = loyalty_redemption_account
        if loyalty_redemption_cost_center:
            invoice.loyalty_redemption_cost_center = loyalty_redemption_cost_center
        # Set loyalty_amount so ERPNext includes it in paid_amount calculation.
        # Without this, validate_full_payment() rejects the invoice when
        # Allow Partial Payment is unchecked (paid_amount < grand_total).
        if loyalty_program:
            conversion_factor = flt(
                frappe.db.get_value("Loyalty Program", loyalty_program, "conversion_factor")
            )
            if conversion_factor:
                invoice.loyalty_amount = flt(invoice.loyalty_points * conversion_factor)

    # Return
    if is_return:
        invoice.is_return = 1
        if return_against:
            invoice.return_against = return_against

    # Campaign from profile (v14/v15: campaign, v16: utm_campaign)
    set_campaign_from_profile(invoice, profile)

    # Set all optional fields (address, contact, currency, commission,
    # document details, posting, naming, shipping, terms, printing,
    # payment terms, write-off, sales team)
    set_invoice_optional_fields(
        invoice,
        profile,
        customer_address=customer_address,
        shipping_address_name=shipping_address_name,
        contact_person=contact_person,
        conversion_rate=conversion_rate,
        price_list_currency=price_list_currency,
        plc_conversion_rate=plc_conversion_rate,
        sales_partner=sales_partner,
        commission_rate=commission_rate,
        project=project,
        cost_center=cost_center,
        remarks=remarks,
        po_no=po_no,
        po_date=po_date,
        set_posting_time=set_posting_time,
        posting_date=posting_date,
        posting_time=posting_time,
        naming_series=naming_series,
        shipping_rule=shipping_rule,
        tc_name=tc_name,
        terms=terms,
        letter_head=letter_head,
        select_print_heading=select_print_heading,
        group_same_items=group_same_items,
        language=language,
        payment_terms_template=payment_terms_template,
        allocate_advances_automatically=allocate_advances_automatically,
        write_off_amount=write_off_amount,
        write_off_outstanding_amount_automatically=write_off_outstanding_amount_automatically,
        debit_to=debit_to,
        sales_team=sales_team,
    )

    # Validate stock availability before submission
    if profile.validate_stock_on_save:
        for item_data in items:
            item_code = item_data.get("item_code")
            qty = safe_float(item_data.get("qty", 1))
            item_warehouse = item_data.get("warehouse") or profile.warehouse

            # Product Bundle: validate component stock instead
            bundle_components = get_product_bundle_items(item_code)
            if bundle_components:
                validate_bundle_stock(item_code, qty, item_warehouse)
                continue

            is_stock_item = frappe.db.get_value("Item", item_code, "is_stock_item")
            if not is_stock_item:
                continue
            actual_qty = frappe.db.get_value(
                "Bin", {"item_code": item_code, "warehouse": item_warehouse}, "actual_qty"
            ) or 0
            if qty > actual_qty:
                frappe.throw(
                    _("{0}: Insufficient stock. Available: {1}, Requested: {2}").format(
                        item_code, actual_qty, qty
                    )
                )

    # Store credit via advance Payment Entries
    store_credit = flt(store_credit_amount)
    credit_data = None
    if store_credit > 0:
        from pos_prime.api.customer_profile import get_store_credit

        credit_data = get_store_credit(customer, profile.company)
        available = flt(credit_data.get("total_advance", 0))
        if store_credit > available:
            store_credit = available

    invoice.flags.ignore_permissions = True
    invoice.set_missing_values()

    # Cap payment row amounts so total paid does not exceed the invoice total.
    # When a customer tenders more cash than the bill (e.g. pays 1000 for an
    # 880 bill), the frontend shows the change but the backend should record
    # only the net amount.  Without this cap, ERPNext's POS Closing Entry
    # get_payments() may fail to subtract change_amount (due to
    # account_for_change_amount vs payment-account mismatch), inflating the
    # expected cash and showing a false shortage.
    if not is_return and flt(invoice.change_amount) > 0:
        excess = flt(invoice.change_amount)
        for p in reversed(invoice.payments):
            if excess <= 0:
                break
            reduction = min(excess, flt(p.amount))
            p.amount = flt(p.amount - reduction)
            excess -= reduction

    # Now grand_total is calculated — cap store credit and allocate advances FIFO
    if store_credit > 0 and credit_data:
        invoice_total = flt(invoice.rounded_total or invoice.grand_total)
        if invoice_total > 0:
            store_credit = min(store_credit, invoice_total)

        remaining = store_credit
        for adv in credit_data.get("advances", []):
            if remaining <= 0:
                break
            alloc = min(remaining, flt(adv.amount))
            if alloc <= 0:
                continue
            invoice.append("advances", {
                "reference_type": adv.reference_type,
                "reference_name": adv.reference_name,
                "reference_row": adv.get("reference_row") or None,
                "advance_amount": flt(adv.amount),
                "allocated_amount": alloc,
                "remarks": adv.get("remarks", ""),
            })
            remaining -= alloc

        invoice.total_advance = flt(store_credit - remaining)

    # Override POS validation to account for advance payments
    if flt(invoice.total_advance) > 0:
        _orig_validate_full = invoice.validate_full_payment

        def _patched_validate_full():
            effective_paid = flt(invoice.paid_amount) + flt(invoice.total_advance)
            target = flt(invoice.rounded_total or invoice.grand_total)
            if effective_paid >= target:
                return
            _orig_validate_full()

        invoice.validate_full_payment = _patched_validate_full

        def _patched_set_outstanding():
            invoice.outstanding_amount = max(
                0,
                flt(invoice.rounded_total or invoice.grand_total)
                - flt(invoice.paid_amount)
                - flt(invoice.total_advance)
                + flt(invoice.change_amount)
                + flt(invoice.write_off_amount),
            )

        invoice.set_outstanding_amount = _patched_set_outstanding

    # When "Validate Stock on Save" is unchecked, bypass ERPNext's
    # validate_stock_availablility() which runs on both insert and submit.
    if not profile.validate_stock_on_save:
        invoice.validate_stock_availablility = lambda: None

    invoice.insert()
    invoice.submit()

    # Allocate advances — reduce unallocated_amount to prevent double-spend
    # Payment Entries: reduce unallocated_amount directly
    # Journal Entries: tracked via the advances child table (allocation subquery)
    if flt(invoice.total_advance) > 0:
        for adv_row in invoice.advances:
            allocated = flt(adv_row.allocated_amount)
            if allocated <= 0:
                continue
            if adv_row.reference_type == "Payment Entry":
                pe_unallocated = flt(
                    frappe.db.get_value(
                        "Payment Entry", adv_row.reference_name, "unallocated_amount"
                    )
                )
                new_unallocated = max(0, pe_unallocated - allocated)
                frappe.db.set_value(
                    "Payment Entry",
                    adv_row.reference_name,
                    "unallocated_amount",
                    new_unallocated,
                    update_modified=False,
                )

    return format_invoice_response(invoice)
