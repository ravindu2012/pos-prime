import frappe


@frappe.whitelist()
def get_payment_methods(pos_profile):
    """Get allowed payment methods for a POS Profile."""
    if not frappe.db.exists("POS Profile", pos_profile):
        frappe.throw(f"POS Profile '{pos_profile}' does not exist")
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
