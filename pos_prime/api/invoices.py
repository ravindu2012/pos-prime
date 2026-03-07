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

    if not payments and not getattr(profile, "allow_partial_payment", 0) and not flt(store_credit_amount):
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

    # Validate and cap store credit at submit time to prevent double-spend
    store_credit = flt(store_credit_amount)
    if store_credit > 0:
        from pos_prime.api.customer_profile import get_store_credit

        actual = get_store_credit(customer, profile.company)
        available = flt(actual.get("store_credit", 0))
        if store_credit > available:
            store_credit = available
        # Cap to invoice total
        invoice_total = flt(invoice.grand_total) or flt(invoice.net_total) or 0
        if invoice_total > 0:
            store_credit = min(store_credit, invoice_total)

    invoice.flags.ignore_permissions = True
    invoice.set_missing_values()
    invoice.insert()
    invoice.submit()

    # After submit, set outstanding_amount = store_credit amount.
    # POS Invoices don't create GL entries until consolidation, so we use
    # outstanding_amount to track how much store credit was "claimed".
    # get_store_credit() subtracts this from the GL credit balance.
    if store_credit > 0:
        outstanding = flt(store_credit, invoice.precision("outstanding_amount"))
        if outstanding > 0:
            invoice.db_set("outstanding_amount", outstanding, update_modified=False)
            invoice.outstanding_amount = outstanding
            invoice.set_status(update=True)

    return format_invoice_response(invoice)
