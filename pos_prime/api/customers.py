# Copyright (c) 2026, Ravindu Gajanayaka
# Licensed under GPLv3. See license.txt

import re
import frappe
from frappe import _
from pos_prime.api._utils import validate_pos_access


@frappe.whitelist()
def search_customers(search_term="", pos_profile=""):
    """Search customers by name, phone, or email.

    If pos_profile has customer_groups configured, only returns customers
    belonging to those groups.

    Phone numbers are normalized so local format (07xxxxxxxx) matches
    international format (+947xxxxxxxx) and vice versa.
    """
    validate_pos_access(pos_profile or None)
    if not search_term or len(search_term) < 2:
        return []

    search = f"%{search_term}%"

    # Normalize phone: extract last 9 digits to match regardless of country code
    digits_only = re.sub(r"\D", "", search_term)
    phone_suffix_condition = ""
    params = {"search": search}

    if len(digits_only) >= 7:
        core_digits = digits_only[-9:]
        params["phone_suffix"] = f"%{core_digits}"
        phone_suffix_condition = "OR mobile_no LIKE %(phone_suffix)s"

    # Check if POS Profile restricts customer groups
    group_filter = ""

    if pos_profile:
        profile_groups = frappe.get_all(
            "POS Customer Group",
            filters={"parent": pos_profile, "parenttype": "POS Profile"},
            pluck="customer_group",
        )
        if profile_groups:
            group_filter = "AND customer_group IN %(groups)s"
            params["groups"] = profile_groups

    customers = frappe.db.sql(
        f"""
        SELECT name, customer_name, mobile_no, email_id
        FROM `tabCustomer`
        WHERE disabled = 0
        {group_filter}
        AND (
            customer_name LIKE %(search)s
            OR name LIKE %(search)s
            OR mobile_no LIKE %(search)s
            OR email_id LIKE %(search)s
            {phone_suffix_condition}
        )
        ORDER BY customer_name ASC
        LIMIT 20
    """,
        params,
        as_dict=True,
    )

    return customers


@frappe.whitelist()
def get_recent_customers(pos_profile="", limit=20):
    """Return customers who had recent POS invoices, ordered by latest transaction.

    If pos_profile is provided, only returns customers with invoices from that
    profile's company, and respects customer_group filtering.
    """
    validate_pos_access(pos_profile or None)
    params = {"limit": int(limit)}
    company_filter = ""
    group_filter = ""

    if pos_profile:
        company = frappe.db.get_value("POS Profile", pos_profile, "company")
        if company:
            company_filter = "AND inv.company = %(company)s"
            params["company"] = company

        profile_groups = frappe.get_all(
            "POS Customer Group",
            filters={"parent": pos_profile, "parenttype": "POS Profile"},
            pluck="customer_group",
        )
        if profile_groups:
            group_filter = "AND c.customer_group IN %(groups)s"
            params["groups"] = profile_groups

    return frappe.db.sql(
        f"""
        SELECT c.name, c.customer_name, c.mobile_no, c.email_id,
               MAX(inv.posting_date) AS last_invoice_date
        FROM `tabCustomer` c
        INNER JOIN `tabPOS Invoice` inv ON inv.customer = c.name
        WHERE c.disabled = 0
          AND inv.docstatus = 1
          {company_filter}
          {group_filter}
        GROUP BY c.name
        ORDER BY last_invoice_date DESC
        LIMIT %(limit)s
    """,
        params,
        as_dict=True,
    )


@frappe.whitelist()
def get_customer(customer_name):
    """Get customer details for POS.

    Returns essential customer fields without requiring direct Customer
    doctype read permission (uses ignore_permissions internally).
    """
    validate_pos_access()
    if not frappe.db.exists("Customer", customer_name):
        frappe.throw(_("Customer {0} does not exist").format(customer_name))

    data = frappe.db.get_value(
        "Customer",
        customer_name,
        [
            "name", "customer_name", "email_id", "mobile_no",
            "loyalty_program", "territory", "customer_group", "tax_id",
        ],
        as_dict=True,
    )
    return data


@frappe.whitelist()
def get_quick_entry_options(pos_profile=""):
    """Return dropdown options needed for the new-customer quick entry dialog.

    Returns customer_groups, customer_type options, and quick_entry fields
    from the Customer doctype meta so the frontend can render a matching form.
    """
    validate_pos_access(pos_profile or None)

    # Customer groups — prefer POS Profile groups, fall back to leaf groups
    customer_groups = []
    if pos_profile:
        customer_groups = frappe.get_all(
            "POS Customer Group",
            filters={"parent": pos_profile, "parenttype": "POS Profile"},
            pluck="customer_group",
        )
    if not customer_groups:
        customer_groups = frappe.get_list(
            "Customer Group",
            filters={"is_group": 0},
            pluck="name",
            order_by="name asc",
            limit_page_length=50,
        )

    # Customer type options from the Select field
    meta = frappe.get_meta("Customer")
    ct_field = meta.get_field("customer_type")
    customer_types = (ct_field.options or "").split("\n") if ct_field else ["Individual"]

    # Quick entry fields (reqd or allow_in_quick_entry)
    quick_fields = []
    for f in meta.fields:
        if (f.reqd or f.allow_in_quick_entry) and not f.read_only and f.fieldtype not in (
            "Tab Break", "Section Break", "Column Break", "Table",
        ):
            quick_fields.append({
                "fieldname": f.fieldname,
                "label": f.label,
                "fieldtype": f.fieldtype,
                "options": f.options,
                "reqd": f.reqd,
                "default": f.default,
            })

    # Country options for address
    countries = frappe.get_list(
        "Country", pluck="name", order_by="name asc", limit_page_length=0,
    )

    # Default country from system settings
    default_country = frappe.db.get_default("country") or ""

    # Defaults
    default_group = (
        frappe.db.get_single_value("Selling Settings", "customer_group")
        or (customer_groups[0] if customer_groups else "")
    )

    return {
        "customer_groups": customer_groups,
        "customer_types": [t for t in customer_types if t.strip()],
        "quick_fields": quick_fields,
        "default_customer_group": default_group,
        "default_customer_type": "Individual",
        "default_territory": frappe.db.get_single_value("Selling Settings", "territory")
            or "All Territories",
        "countries": countries,
        "default_country": default_country,
    }


@frappe.whitelist()
def quick_create_customer(customer_name, mobile_no=None, email_id=None,
                          customer_type=None, customer_group=None,
                          territory=None, pos_profile="",
                          first_name=None, last_name=None,
                          address_line1=None, address_line2=None,
                          city=None, state=None, pincode=None, country=None,
                          **extra_fields):
    """Create a customer record from the POS quick entry dialog.

    Accepts all quick_entry fields from the Customer doctype plus
    contact (first_name, last_name) and address fields. ERPNext's
    Customer on_update hook auto-creates Contact and Address records.
    """
    validate_pos_access(pos_profile or None)
    if not customer_name or not customer_name.strip():
        frappe.throw(_("Customer name is required"))

    customer_name = customer_name.strip()

    if len(customer_name) > 140:
        frappe.throw(_("Customer name must not exceed 140 characters"))

    if email_id:
        email_pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email_id):
            frappe.throw(_("Invalid email address format"))

    # Resolve defaults
    if not customer_group and pos_profile:
        profile_groups = frappe.get_all(
            "POS Customer Group",
            filters={"parent": pos_profile, "parenttype": "POS Profile"},
            pluck="customer_group",
            limit=1,
        )
        if profile_groups:
            customer_group = profile_groups[0]

    doc_data = {
        "doctype": "Customer",
        "customer_name": customer_name,
        "customer_type": customer_type or "Individual",
        "customer_group": customer_group
            or frappe.db.get_single_value("Selling Settings", "customer_group")
            or "All Customer Groups",
        "territory": territory
            or frappe.db.get_single_value("Selling Settings", "territory")
            or "All Territories",
    }

    if mobile_no:
        doc_data["mobile_no"] = mobile_no
    if email_id:
        doc_data["email_id"] = email_id

    # Contact name fields — Customer on_update uses these to create Contact
    if first_name:
        doc_data["first_name"] = first_name
    if last_name:
        doc_data["last_name"] = last_name

    # Address fields — Customer on_update uses these to create Address
    if address_line1:
        doc_data["address_line1"] = address_line1
    if address_line2:
        doc_data["address_line2"] = address_line2
    if city:
        doc_data["city"] = city
    if state:
        doc_data["state"] = state
    if pincode:
        doc_data["pincode"] = pincode
    if country:
        doc_data["country"] = country

    # Apply any extra quick_entry fields (e.g. custom_nic_number)
    meta = frappe.get_meta("Customer")
    allowed_quick = {
        f.fieldname for f in meta.fields
        if (f.reqd or f.allow_in_quick_entry)
        and not f.read_only
        and f.fieldtype not in ("Tab Break", "Section Break", "Column Break", "Table")
    }
    for key, value in extra_fields.items():
        if key in allowed_quick and value:
            doc_data[key] = value

    customer = frappe.get_doc(doc_data)
    customer.insert(ignore_permissions=True)

    return customer.name


@frappe.whitelist()
def update_customer_field(customer, fieldname, value=""):
    """Update a customer contact field from POS.

    Mirrors ERPNext's built-in POS approach: updates both the Contact doctype
    (primary contact with email_ids/phone_nos child tables) and the Customer
    doctype's denormalized fields.
    """
    validate_pos_access()

    allowed_fields = {"email_id", "mobile_no", "loyalty_program"}
    if fieldname not in allowed_fields:
        frappe.throw(_("Field {0} cannot be updated from POS").format(fieldname))

    if not frappe.db.exists("Customer", customer):
        frappe.throw(_("Customer {0} does not exist").format(customer))

    if fieldname == "email_id" and value:
        email_pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, value):
            frappe.throw(_("Invalid email address format"))

    if fieldname == "loyalty_program":
        frappe.db.set_value("Customer", customer, "loyalty_program", value)
        return customer

    # Get or create primary contact (same logic as ERPNext's set_customer_info)
    contact = frappe.get_cached_value("Customer", customer, "customer_primary_contact")

    if not contact:
        contacts = frappe.db.sql(
            """
            SELECT parent FROM `tabDynamic Link`
            WHERE parenttype = 'Contact'
              AND parentfield = 'links'
              AND link_doctype = 'Customer'
              AND link_name = %s
            """,
            (customer,),
            as_dict=True,
        )
        contact = contacts[0].get("parent") if contacts else None

    if not contact:
        new_contact = frappe.new_doc("Contact")
        new_contact.is_primary_contact = 1
        new_contact.first_name = frappe.db.get_value("Customer", customer, "customer_name") or customer
        new_contact.set("links", [{"link_doctype": "Customer", "link_name": customer}])
        new_contact.save(ignore_permissions=True)
        contact = new_contact.name
        frappe.db.set_value("Customer", customer, "customer_primary_contact", contact)

    # Update the Contact doctype and Customer denormalized field
    contact_doc = frappe.get_doc("Contact", contact)

    if fieldname == "email_id":
        contact_doc.set("email_ids", [{"email_id": value, "is_primary": 1}] if value else [])
        frappe.db.set_value("Customer", customer, "email_id", value)
    elif fieldname == "mobile_no":
        contact_doc.set("phone_nos", [{"phone": value, "is_primary_mobile_no": 1}] if value else [])
        frappe.db.set_value("Customer", customer, "mobile_no", value)

    contact_doc.save(ignore_permissions=True)

    return customer
