import frappe
from frappe import _


@frappe.whitelist()
def get_batch_nos(item_code, warehouse):
    """Get available batches for an item in a warehouse with qty and expiry."""
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
            AND b.disabled = 0
            AND (b.expiry_date IS NULL OR b.expiry_date >= CURDATE())
        GROUP BY sle.batch_no
        HAVING SUM(sle.actual_qty) > 0
        ORDER BY b.expiry_date ASC, b.creation ASC
        """,
        {"item_code": item_code, "warehouse": warehouse},
        as_dict=True,
    )

    return batches


@frappe.whitelist()
def get_serial_nos(item_code, warehouse, batch_no=None):
    """Get available serial numbers for an item in a warehouse."""
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
def get_item_uoms(item_code):
    """Get available UOMs for an item with conversion factors."""
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
