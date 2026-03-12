# Copyright (c) 2026, Ravindu Gajanayaka
# Licensed under GPLv3. See license.txt

import frappe


@frappe.whitelist()
def get_customer_addresses(customer):
    """Get all addresses linked to a customer."""
    if not frappe.db.exists("Customer", customer):
        return []

    address_names = frappe.get_all(
        "Dynamic Link",
        filters={"link_doctype": "Customer", "link_name": customer, "parenttype": "Address"},
        pluck="parent",
    )
    if not address_names:
        return []

    addresses = frappe.get_all(
        "Address",
        filters={"name": ["in", address_names]},
        fields=["name", "address_title", "address_type", "address_line1", "address_line2",
                "city", "state", "pincode", "country", "phone", "email_id",
                "is_primary_address", "is_shipping_address"],
    )
    for addr in addresses:
        try:
            addr["display"] = frappe.get_doc("Address", addr.name).get_display()
        except Exception:
            addr["display"] = addr.get("address_line1") or addr.name
    return addresses


@frappe.whitelist()
def get_customer_contacts(customer):
    """Get all contacts linked to a customer."""
    if not frappe.db.exists("Customer", customer):
        return []

    contact_names = frappe.get_all(
        "Dynamic Link",
        filters={"link_doctype": "Customer", "link_name": customer, "parenttype": "Contact"},
        pluck="parent",
    )
    if not contact_names:
        return []

    contacts = frappe.get_all(
        "Contact",
        filters={"name": ["in", contact_names]},
        fields=["name", "first_name", "last_name", "email_id", "phone", "mobile_no",
                "is_primary_contact", "is_billing_contact"],
    )
    for c in contacts:
        c["full_name"] = f"{c.first_name or ''} {c.last_name or ''}".strip()
    return contacts
