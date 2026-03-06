import frappe
from frappe import _
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
def save_draft_invoice(
    customer,
    pos_profile,
    items,
    payments=None,
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
    # Payment terms
    payment_terms_template=None,
    # Discount
    additional_discount_percentage=0,
    discount_amount=0,
    apply_discount_on="Grand Total",
    coupon_code=None,
):
    """Save a POS Invoice as draft (insert without submit).

    Supports all optional fields for full POS Invoice parity.
    """
    # Permission check
    validate_pos_access(pos_profile)

    if isinstance(items, str):
        items = json.loads(items)
    if isinstance(payments, str):
        payments = json.loads(payments)

    # Input validation
    if not items:
        frappe.throw(_("Items cannot be empty"))

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
            "update_stock": 1,
            "account_for_change_amount": profile.account_for_change_amount
            or profile.write_off_account,
            "write_off_account": profile.write_off_account,
            "write_off_cost_center": profile.write_off_cost_center,
            "ignore_pricing_rule": 1 if profile.ignore_pricing_rule else 0,
            "disable_rounded_total": 1 if profile.disable_rounded_total else 0,
        }
    )

    # Company address from POS Profile
    if profile.company_address:
        invoice.company_address = profile.company_address

    for item_data in items:
        invoice.append("items", build_item_dict(item_data, profile))

    if payments:
        for payment_data in payments:
            invoice.append(
                "payments",
                {
                    "mode_of_payment": payment_data.get("mode_of_payment"),
                    "amount": safe_float(payment_data.get("amount", 0)),
                },
            )

    # POS Invoice requires at least one payment entry even for drafts
    if not invoice.payments:
        default_mop = (profile.payments[0].mode_of_payment if profile.payments else "Cash")
        invoice.append("payments", {"mode_of_payment": default_mop, "amount": 0})

    # Set taxes template
    if profile.taxes_and_charges:
        invoice.taxes_and_charges = profile.taxes_and_charges
    if profile.tax_category:
        invoice.tax_category = profile.tax_category

    # Campaign from profile (v14/v15: campaign, v16: utm_campaign)
    set_campaign_from_profile(invoice, profile)

    # Discounts
    if additional_discount_percentage:
        invoice.additional_discount_percentage = safe_float(additional_discount_percentage)
    if discount_amount:
        invoice.discount_amount = safe_float(discount_amount)
    if apply_discount_on:
        invoice.apply_discount_on = apply_discount_on
    if coupon_code:
        invoice.coupon_code = coupon_code

    # Set all optional fields
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
    )

    invoice.flags.ignore_permissions = True
    invoice.set_missing_values()
    invoice.insert()
    # Do NOT submit -- leave as draft

    return format_invoice_response(invoice)


@frappe.whitelist()
def get_draft_invoices(pos_profile):
    """List draft POS Invoices for the current POS profile."""
    validate_pos_access(pos_profile)

    drafts = frappe.get_list(
        "POS Invoice",
        filters={
            "pos_profile": pos_profile,
            "docstatus": 0,
        },
        fields=[
            "name",
            "customer",
            "customer_name",
            "grand_total",
            "net_total",
            "posting_date",
            "posting_time",
            "creation",
            "owner",
            "modified",
            "currency",
            "total_qty",
            "status",
            "remarks",
            "sales_partner",
            "po_no",
            "project",
        ],
        order_by="creation desc",
    )

    # Batch fetch item counts in a single query instead of per-draft
    if drafts:
        draft_names = [d.name for d in drafts]
        item_counts = frappe.db.sql(
            """SELECT parent, COUNT(*) as cnt
               FROM `tabPOS Invoice Item`
               WHERE parent IN %(names)s
               GROUP BY parent""",
            {"names": draft_names},
            as_dict=True,
        )
        count_map = {r.parent: r.cnt for r in item_counts}
        for draft in drafts:
            draft["item_count"] = count_map.get(draft.name, 0)

    return drafts


@frappe.whitelist()
def load_draft_invoice(invoice_name):
    """Load a full draft invoice with all items, payments, and fields."""
    if not frappe.has_permission("POS Invoice", "read", invoice_name):
        frappe.throw(
            _("You do not have permission to view this invoice."),
            frappe.PermissionError,
        )

    invoice = frappe.get_doc("POS Invoice", invoice_name)

    if invoice.docstatus != 0:
        frappe.throw(_("Invoice {0} is not a draft").format(invoice_name))

    return format_invoice_response(invoice)


@frappe.whitelist()
def delete_draft_invoice(invoice_name):
    """Delete a draft POS Invoice."""
    invoice = frappe.get_doc("POS Invoice", invoice_name)

    if invoice.docstatus != 0:
        frappe.throw(_("Only draft invoices can be deleted"))

    # Ownership / POS profile scope check: only owner or System Manager can delete
    if invoice.owner != frappe.session.user and "System Manager" not in frappe.get_roles():
        frappe.throw(
            _("You can only delete your own draft invoices."),
            frappe.PermissionError,
        )

    frappe.delete_doc("POS Invoice", invoice_name, force=True)
    return {"success": True}


@frappe.whitelist()
def update_and_submit_draft(
    invoice_name,
    customer,
    items,
    payments,
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
    # Shipping & terms
    shipping_rule=None,
    tc_name=None,
    terms=None,
    # Printing
    letter_head=None,
    select_print_heading=None,
    group_same_items=False,
    language=None,
    # Payment terms
    payment_terms_template=None,
    allocate_advances_automatically=False,
    # Write-off
    write_off_amount=0,
    debit_to=None,
    # Sales team
    sales_team=None,
):
    """Update a draft invoice with all fields and submit it."""
    validate_pos_access()
    if isinstance(items, str):
        items = json.loads(items)
    if isinstance(payments, str):
        payments = json.loads(payments)
    if isinstance(sales_team, str):
        sales_team = json.loads(sales_team)

    # Input validation
    if not items:
        frappe.throw(_("Items cannot be empty"))
    if not payments:
        frappe.throw(_("Payments cannot be empty"))

    invoice = frappe.get_doc("POS Invoice", invoice_name)

    if invoice.docstatus != 0:
        frappe.throw(_("Invoice {0} is not a draft").format(invoice_name))

    invoice.customer = customer

    # Clear and re-add items
    invoice.items = []
    profile = frappe.get_doc("POS Profile", invoice.pos_profile)

    for item_data in items:
        invoice.append("items", build_item_dict(item_data, profile))

    # Clear and re-add payments
    invoice.payments = []
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

    invoice.paid_amount = total_paid

    # Taxes
    if taxes:
        invoice.taxes_and_charges = taxes

    # Discounts
    if additional_discount_percentage:
        invoice.additional_discount_percentage = safe_float(additional_discount_percentage)
    if discount_amount:
        invoice.discount_amount = safe_float(discount_amount)
    if apply_discount_on:
        invoice.apply_discount_on = apply_discount_on
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

    # Set all optional fields
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
        debit_to=debit_to,
        sales_team=sales_team,
    )

    # Apply disable_rounded_total from profile
    if profile.disable_rounded_total:
        invoice.disable_rounded_total = 1

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

    invoice.flags.ignore_permissions = True
    invoice.set_missing_values()
    invoice.save()
    invoice.submit()

    return format_invoice_response(invoice)
