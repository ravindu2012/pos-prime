# Copyright (c) 2026, Ravindu Gajanayaka
# Licensed under GPLv3. See license.txt

import frappe
from pos_prime.api._utils import validate_pos_access


@frappe.whitelist()
def get_payment_methods(pos_profile):
    """Get allowed payment methods for a POS Profile."""
    validate_pos_access(pos_profile)
    profile = frappe.get_doc("POS Profile", pos_profile)
    methods = []
    for pm in profile.payments:
        methods.append(
            {
                "mode_of_payment": pm.mode_of_payment,
                "default": pm.default,
            }
        )
    return methods
