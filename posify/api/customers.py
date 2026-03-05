import re
import frappe
from frappe import _


@frappe.whitelist()
def search_customers(search_term="", pos_profile=""):
    """Search customers by name, phone, or email.

    If pos_profile has customer_groups configured, only returns customers
    belonging to those groups.

    Phone numbers are normalized so local format (07xxxxxxxx) matches
    international format (+947xxxxxxxx) and vice versa.
    """
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
def quick_create_customer(customer_name, mobile_no=None, email_id=None):
    """Create a minimal customer record."""
    if not customer_name:
        frappe.throw(_("Customer name is required"))

    if len(customer_name) > 140:
        frappe.throw(_("Customer name must not exceed 140 characters"))

    if email_id:
        email_pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email_id):
            frappe.throw(_("Invalid email address format"))

    customer = frappe.get_doc(
        {
            "doctype": "Customer",
            "customer_name": customer_name,
            "customer_type": "Individual",
            "customer_group": frappe.db.get_single_value(
                "Selling Settings", "customer_group"
            )
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
