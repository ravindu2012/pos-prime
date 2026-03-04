import frappe
from frappe import _


@frappe.whitelist()
def get_customer_loyalty(customer):
    """Get loyalty program data for a customer."""
    try:
        if not frappe.db.exists("Customer", customer):
            frappe.throw(_("Customer {0} does not exist").format(customer))

        customer_doc = frappe.get_doc("Customer", customer)

        if not customer_doc.loyalty_program:
            return None

        loyalty_program = frappe.get_doc("Loyalty Program", customer_doc.loyalty_program)

        # Get customer's current loyalty points (include NULL expiry = lifetime points)
        loyalty_points = frappe.db.sql(
            """
            SELECT SUM(loyalty_points) as points
            FROM `tabLoyalty Point Entry`
            WHERE customer = %(customer)s
                AND loyalty_program = %(program)s
                AND (expiry_date IS NULL OR expiry_date >= CURDATE())
            """,
            {"customer": customer, "program": customer_doc.loyalty_program},
            as_dict=True,
        )

        points = (loyalty_points[0].points or 0) if loyalty_points else 0

        # Get conversion factor (points to currency)
        conversion_factor = 0
        expense_account = ""
        cost_center = ""

        if loyalty_program.loyalty_program_type == "Single Tier":
            # Single Tier programs have one rule — use the first available
            if loyalty_program.collection_rules:
                conversion_factor = loyalty_program.collection_rules[0].conversion_factor or 0
        elif loyalty_program.loyalty_program_type == "Multiple Tier":
            # For multi-tier, use the first rule as default conversion
            if loyalty_program.collection_rules:
                conversion_factor = loyalty_program.collection_rules[0].conversion_factor or 0

        # Get expense account from loyalty program
        expense_account = loyalty_program.expense_account or ""
        cost_center = loyalty_program.cost_center or ""

        return {
            "loyalty_program": customer_doc.loyalty_program,
            "loyalty_points": points,
            "conversion_factor": conversion_factor,
            "expense_account": expense_account,
            "cost_center": cost_center,
            "max_redeemable_amount": points * conversion_factor if conversion_factor else 0,
        }
    except frappe.DoesNotExistError:
        raise
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Posify: get_customer_loyalty failed")
        frappe.throw(_("Failed to fetch loyalty data: {0}").format(str(e)))
