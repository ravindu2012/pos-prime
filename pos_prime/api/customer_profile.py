# Copyright (c) 2026, Ravindu Gajanayaka
# Licensed under GPLv3. See license.txt

import frappe
from frappe.utils import flt


@frappe.whitelist()
def get_store_credit(customer, company):
    """Get available store credit from unallocated Payment Entries and Journal Entries.

    Returns individual advances (for populating the advances table on
    POS Invoice) and the total available amount.
    """
    if not customer or not company:
        return {"advances": [], "total_advance": 0}

    if not frappe.db.exists("Customer", customer):
        return {"advances": [], "total_advance": 0}

    # 1. Payment Entry advances (unallocated receipts)
    pe_advances = frappe.db.sql(
        """
        SELECT
            'Payment Entry' as reference_type,
            pe.name as reference_name,
            '' as reference_row,
            pe.unallocated_amount as amount,
            pe.remarks,
            pe.posting_date
        FROM `tabPayment Entry` pe
        WHERE pe.party_type = 'Customer'
          AND pe.party = %(customer)s
          AND pe.company = %(company)s
          AND pe.payment_type = 'Receive'
          AND pe.docstatus = 1
          AND pe.unallocated_amount > 0
        ORDER BY pe.posting_date ASC
        """,
        {"customer": customer, "company": company},
        as_dict=True,
    )

    # 2. Journal Entry advances (manual credits, adjustments)
    receivable_account = frappe.get_cached_value(
        "Company", company, "default_receivable_account"
    )
    je_advances = []
    if receivable_account:
        je_advances = frappe.db.sql(
            """
            SELECT
                'Journal Entry' as reference_type,
                jea.parent as reference_name,
                jea.name as reference_row,
                (jea.credit_in_account_currency - jea.debit_in_account_currency
                 - IFNULL(alloc.total_allocated, 0)) as amount,
                je.remark as remarks,
                je.posting_date
            FROM `tabJournal Entry Account` jea
            JOIN `tabJournal Entry` je ON je.name = jea.parent
            LEFT JOIN (
                SELECT reference_row, SUM(allocated_amount) as total_allocated
                FROM `tabSales Invoice Advance`
                WHERE reference_type = 'Journal Entry' AND docstatus = 1
                GROUP BY reference_row
            ) alloc ON alloc.reference_row = jea.name
            WHERE jea.party_type = 'Customer'
              AND jea.party = %(customer)s
              AND je.company = %(company)s
              AND jea.account = %(receivable_account)s
              AND je.docstatus = 1
              AND jea.is_advance = 'Yes'
              AND (jea.credit_in_account_currency - jea.debit_in_account_currency
                   - IFNULL(alloc.total_allocated, 0)) > 0
            ORDER BY je.posting_date ASC
            """,
            {
                "customer": customer,
                "company": company,
                "receivable_account": receivable_account,
            },
            as_dict=True,
        )

    # Combine and sort by posting date (FIFO)
    advances = sorted(
        list(pe_advances) + list(je_advances),
        key=lambda a: a.posting_date or "",
    )
    total = sum(flt(a.amount) for a in advances)
    return {"advances": advances, "total_advance": flt(total, 2)}


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
