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
def quick_create_customer(customer_name, mobile_no=None, email_id=None, pos_profile=""):
    """Create a minimal customer record.

    If pos_profile is provided, uses the first customer_group from the POS Profile
    and the company's default territory instead of global Selling Settings.
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

    customer_group = None

    if pos_profile:
        profile_groups = frappe.get_all(
            "POS Customer Group",
            filters={"parent": pos_profile, "parenttype": "POS Profile"},
            pluck="customer_group",
            limit=1,
        )
        if profile_groups:
            customer_group = profile_groups[0]

    customer = frappe.get_doc(
        {
            "doctype": "Customer",
            "customer_name": customer_name,
            "customer_type": "Individual",
            "customer_group": customer_group
            or frappe.db.get_single_value("Selling Settings", "customer_group")
            or "All Customer Groups",
            "territory": frappe.db.get_single_value("Selling Settings", "territory")
            or "All Territories",
        }
    )

    if mobile_no:
        customer.mobile_no = mobile_no
    if email_id:
        customer.email_id = email_id

    customer.insert(ignore_permissions=True)

    return customer.name
