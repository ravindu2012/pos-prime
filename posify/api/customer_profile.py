import frappe


@frappe.whitelist()
def get_customer_pos_invoices(customer, limit=10):
    """Get recent submitted POS Invoices for a customer."""
    if not frappe.db.exists("Customer", customer):
        return []

    limit = min(int(limit), 50)

    invoices = frappe.get_all(
        "POS Invoice",
        filters={"customer": customer, "docstatus": 1},
        fields=[
            "name", "posting_date", "grand_total", "status",
            "is_return", "currency", "total_qty",
        ],
        order_by="posting_date desc, creation desc",
        limit_page_length=limit,
    )
    return invoices


@frappe.whitelist()
def get_customer_outstanding(customer):
    """Get outstanding balance and credit limit for a customer."""
    if not frappe.db.exists("Customer", customer):
        return {"outstanding": 0, "credit_limit": 0}

    # Outstanding from all unpaid Sales/POS Invoices
    result = frappe.db.sql(
        """
        SELECT COALESCE(SUM(outstanding_amount), 0) as outstanding
        FROM `tabSales Invoice`
        WHERE customer = %(customer)s
            AND docstatus = 1
            AND outstanding_amount > 0
        """,
        {"customer": customer},
        as_dict=True,
    )
    outstanding = result[0].outstanding if result else 0

    # Credit limit from Customer Credit Limit child table
    credit_limit = 0
    credit_limits = frappe.get_all(
        "Customer Credit Limit",
        filters={"parent": customer, "parenttype": "Customer"},
        fields=["credit_limit"],
        limit=1,
    )
    if credit_limits:
        credit_limit = credit_limits[0].credit_limit or 0

    return {
        "outstanding": outstanding,
        "credit_limit": credit_limit,
    }
