# Copyright (c) 2026, Ravindu Gajanayaka
# Licensed under GPLv3. See license.txt

import frappe
from frappe import _
from pos_prime.api._utils import validate_pos_access


@frappe.whitelist()
def get_batch_nos(item_code, warehouse):
    """Get available batches for an item in a warehouse with qty and expiry.

    Supports both legacy batch_no on SLE (v14) and serial_and_batch_bundle (v15+).
    """
    validate_pos_access()

    # Try legacy SLE batch_no first
    batches = frappe.db.sql(
        """
        SELECT
            sle.batch_no,
            SUM(sle.actual_qty) as qty,
            b.expiry_date,
            b.batch_qty
        FROM `tabStock Ledger Entry` sle
        INNER JOIN `tabBatch` b ON b.name = sle.batch_no
        WHERE sle.item_code = %(item_code)s
            AND sle.warehouse = %(warehouse)s
            AND sle.is_cancelled = 0
            AND sle.batch_no IS NOT NULL AND sle.batch_no != ''
            AND b.disabled = 0
            AND (b.expiry_date IS NULL OR b.expiry_date >= CURDATE())
        GROUP BY sle.batch_no
        HAVING SUM(sle.actual_qty) > 0
        ORDER BY b.expiry_date ASC, b.creation ASC
        """,
        {"item_code": item_code, "warehouse": warehouse},
        as_dict=True,
    )

    if batches:
        return batches

    # v15+: batch info stored via Serial and Batch Bundle
    if frappe.db.has_column("Stock Ledger Entry", "serial_and_batch_bundle"):
        batches = frappe.db.sql(
            """
            SELECT
                sbe.batch_no,
                SUM(sbe.qty) as qty,
                b.expiry_date,
                b.batch_qty
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabSerial and Batch Entry` sbe
                ON sbe.parent = sle.serial_and_batch_bundle
            INNER JOIN `tabBatch` b ON b.name = sbe.batch_no
            WHERE sle.item_code = %(item_code)s
                AND sle.warehouse = %(warehouse)s
                AND sle.is_cancelled = 0
                AND sle.serial_and_batch_bundle IS NOT NULL
                AND b.disabled = 0
                AND (b.expiry_date IS NULL OR b.expiry_date >= CURDATE())
            GROUP BY sbe.batch_no
            HAVING SUM(sbe.qty) > 0
            ORDER BY b.expiry_date ASC, b.creation ASC
            """,
            {"item_code": item_code, "warehouse": warehouse},
            as_dict=True,
        )

    return batches or []


@frappe.whitelist()
def get_serial_nos(item_code, warehouse, batch_no=None):
    """Get available serial numbers for an item in a warehouse."""
    validate_pos_access()
    filters = {
        "item_code": item_code,
        "warehouse": warehouse,
        "status": "Active",
    }
    if batch_no:
        filters["batch_no"] = batch_no

    serial_nos = frappe.get_list(
        "Serial No",
        filters=filters,
        fields=["name", "batch_no", "warranty_expiry_date"],
        order_by="creation asc",
        limit_page_length=100,
    )

    return serial_nos


@frappe.whitelist()
def auto_fetch_serial_nos(item_code, warehouse, qty, batch_no=None):
    """Auto-fetch available serial numbers for an item (FIFO order).

    Returns up to `qty` active serial numbers from the given warehouse,
    optionally filtered by batch.
    """
    validate_pos_access()
    qty = int(qty)
    if qty <= 0:
        return []

    filters = {
        "item_code": item_code,
        "warehouse": warehouse,
        "status": "Active",
    }
    if batch_no:
        filters["batch_no"] = batch_no

    serial_nos = frappe.get_list(
        "Serial No",
        filters=filters,
        fields=["name"],
        order_by="creation asc",
        limit_page_length=qty,
    )

    return [sn.name for sn in serial_nos]


@frappe.whitelist()
def get_item_uoms(item_code):
    """Get available UOMs for an item with conversion factors."""
    validate_pos_access()
    uoms = frappe.get_all(
        "UOM Conversion Detail",
        filters={"parent": item_code, "parenttype": "Item"},
        fields=["uom", "conversion_factor"],
        order_by="idx asc",
    )

    # Always include stock UOM
    stock_uom = frappe.db.get_value("Item", item_code, "stock_uom")
    if stock_uom and not any(u.uom == stock_uom for u in uoms):
        uoms.insert(0, {"uom": stock_uom, "conversion_factor": 1})

    return uoms
