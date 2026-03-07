import frappe


@frappe.whitelist()
def get_customer_pos_invoices(customer, company="", limit=10):
    """Get recent submitted POS Invoices for a customer.

    If company is provided, only returns invoices from that company.
    """
    if not frappe.db.exists("Customer", customer):
        return []

    limit = min(int(limit), 50)

    filters = {"customer": customer, "docstatus": 1}
    if company:
        filters["company"] = company

    invoices = frappe.get_all(
        "POS Invoice",
        filters=filters,
        fields=[
            "name", "posting_date", "grand_total", "status",
            "is_return", "currency", "total_qty",
        ],
        order_by="posting_date desc, creation desc",
        limit_page_length=limit,
    )
    return invoices


@frappe.whitelist()
def get_customer_outstanding(customer, company=""):
    """Get outstanding balance and credit limit for a customer.

    If company is provided, only calculates outstanding from that company's
    invoices and returns the credit limit for that company.
    """
    if not frappe.db.exists("Customer", customer):
        return {"outstanding": 0, "credit_limit": 0}

    # Outstanding from unpaid Sales Invoices + POS Invoices
    params = {"customer": customer}
    company_filter = ""
    if company:
        company_filter = "AND company = %(company)s"
        params["company"] = company

    result = frappe.db.sql(
        f"""
        SELECT COALESCE(SUM(outstanding_amount), 0) as outstanding
        FROM (
            SELECT outstanding_amount FROM `tabSales Invoice`
            WHERE customer = %(customer)s AND docstatus = 1
                AND outstanding_amount > 0 {company_filter}
            UNION ALL
            SELECT outstanding_amount FROM `tabPOS Invoice`
            WHERE customer = %(customer)s AND docstatus = 1
                AND outstanding_amount > 0
                AND IFNULL(consolidated_invoice, '') = ''
                {company_filter}
        ) combined
        """,
        params,
        as_dict=True,
    )
    outstanding = result[0].outstanding if result else 0

    # Credit limit from Customer Credit Limit child table
    credit_limit = 0
    credit_filters = {"parent": customer, "parenttype": "Customer"}
    if company:
        credit_filters["company"] = company

    credit_limits = frappe.get_all(
        "Customer Credit Limit",
        filters=credit_filters,
        fields=["credit_limit"],
        limit=1,
    )
    if credit_limits:
        credit_limit = credit_limits[0].credit_limit or 0

    return {
        "outstanding": outstanding,
        "credit_limit": credit_limit,
    }
