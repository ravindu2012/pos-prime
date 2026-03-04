import frappe


@frappe.whitelist()
def get_items(
    start=0,
    page_length=20,
    search_term="",
    item_group="",
    pos_profile="",
    hide_unavailable=None,
):
    """Get items for POS with stock quantities and images.

    When hide_unavailable is True (or the POS Profile setting is on),
    only items with stock > 0 in the warehouse are returned — filtered
    server-side so pagination works correctly.
    """
    start = int(start)
    page_length = int(page_length)

    # Load POS Profile settings once
    price_list = "Standard Selling"
    warehouse = ""
    profile_hide = False
    allowed_groups = []

    if pos_profile:
        profile = frappe.get_doc("POS Profile", pos_profile)
        price_list = profile.selling_price_list or "Standard Selling"
        warehouse = profile.warehouse or ""
        profile_hide = bool(profile.get("hide_unavailable_items"))

        # Allowed item groups from POS Profile
        if profile.item_groups:
            allowed_groups = [ig.item_group for ig in profile.item_groups]

    should_hide = hide_unavailable if hide_unavailable is not None else profile_hide

    # ── Build item group filter ──────────────────────────────────────
    group_filter_list = None

    if item_group:
        group_filter_list = _get_group_and_children(item_group)
    elif allowed_groups:
        all_groups = set()
        for grp in allowed_groups:
            all_groups.update(_get_group_and_children(grp))
        group_filter_list = list(all_groups) if all_groups else None

    # ── Build SQL query ──────────────────────────────────────────────
    conditions = ["i.disabled = 0", "i.is_sales_item = 1", "i.has_variants = 0"]
    values = {}

    if group_filter_list:
        conditions.append("i.item_group IN %(groups)s")
        values["groups"] = group_filter_list

    if search_term:
        conditions.append(
            "(i.item_name LIKE %(search)s OR i.item_code LIKE %(search)s OR i.description LIKE %(search)s)"
        )
        values["search"] = f"%{search_term}%"

    if should_hide and warehouse:
        # JOIN with Bin and subtract POS-reserved qty (submitted but
        # unconsolidated POS Invoices) so items sold out in POS are hidden
        # even before consolidation deducts from the stock ledger.
        join_clause = (
            "LEFT JOIN `tabBin` b ON b.item_code = i.item_code AND b.warehouse = %(warehouse)s "
            "LEFT JOIN ("
            "  SELECT pi_item.item_code, SUM(pi_item.stock_qty) as reserved_qty"
            "  FROM `tabPOS Invoice Item` pi_item"
            "  INNER JOIN `tabPOS Invoice` pi ON pi.name = pi_item.parent"
            "  WHERE pi_item.docstatus = 1"
            "    AND pi_item.warehouse = %(warehouse)s"
            "    AND IFNULL(pi.consolidated_invoice, '') = ''"
            "  GROUP BY pi_item.item_code"
            ") pos_res ON pos_res.item_code = i.item_code"
        )
        conditions.append(
            "(i.is_stock_item = 0 OR (IFNULL(b.actual_qty, 0) - IFNULL(pos_res.reserved_qty, 0)) > 0)"
        )
        values["warehouse"] = warehouse
    else:
        join_clause = ""

    where = " AND ".join(conditions)

    items = frappe.db.sql(
        f"""
        SELECT
            i.item_code, i.item_name, i.description, i.item_group,
            i.stock_uom, i.image, i.has_batch_no, i.has_serial_no,
            i.is_stock_item, i.brand, i.weight_per_unit, i.weight_uom
        FROM `tabItem` i
        {join_clause}
        WHERE {where}
        ORDER BY i.item_name ASC
        LIMIT %(start)s, %(page_length)s
        """,
        {**values, "start": start, "page_length": page_length},
        as_dict=True,
    )

    if not items:
        return {"items": []}

    item_codes = [item.item_code for item in items]

    # ── Batch fetch prices ───────────────────────────────────────────
    prices = {
        r.item_code: r.price_list_rate
        for r in frappe.get_all(
            "Item Price",
            filters={
                "item_code": ["in", item_codes],
                "price_list": price_list,
                "selling": 1,
            },
            fields=["item_code", "price_list_rate"],
        )
    }

    # ── Batch fetch stock ────────────────────────────────────────────
    if warehouse:
        stock = {
            r.item_code: r.actual_qty
            for r in frappe.get_all(
                "Bin",
                filters={"item_code": ["in", item_codes], "warehouse": warehouse},
                fields=["item_code", "actual_qty"],
            )
        }
    else:
        stock_data = frappe.db.sql(
            "SELECT item_code, SUM(actual_qty) as qty FROM `tabBin` WHERE item_code IN %s GROUP BY item_code",
            [item_codes],
            as_dict=True,
        )
        stock = {r.item_code: r.qty or 0 for r in stock_data}

    # ── Batch fetch barcodes ─────────────────────────────────────────
    barcodes = {}
    for b in frappe.get_all(
        "Item Barcode",
        filters={"parent": ["in", item_codes]},
        fields=["parent", "barcode"],
        order_by="idx asc",
    ):
        if b.parent not in barcodes:
            barcodes[b.parent] = b.barcode

    # ── Batch fetch tax templates ────────────────────────────────────
    tax_templates = {}
    for t in frappe.get_all(
        "Item Tax",
        filters={"parent": ["in", item_codes]},
        fields=["parent", "item_tax_template"],
        order_by="idx asc",
    ):
        if t.parent not in tax_templates:
            tax_templates[t.parent] = t.item_tax_template

    # ── Batch fetch POS-reserved qty ──────────────────────────────────
    # Submitted but unconsolidated POS Invoices reserve stock that hasn't
    # been deducted from Bin yet (stock ledger updates at consolidation).
    # Subtract reserved qty so the POS shows real available stock.
    reserved = {}
    if warehouse:
        reserved_data = frappe.db.sql(
            """
            SELECT pi_item.item_code, SUM(pi_item.stock_qty) as qty
            FROM `tabPOS Invoice Item` pi_item
            INNER JOIN `tabPOS Invoice` pi ON pi.name = pi_item.parent
            WHERE pi_item.docstatus = 1
              AND pi_item.item_code IN %(item_codes)s
              AND pi_item.warehouse = %(warehouse)s
              AND IFNULL(pi.consolidated_invoice, '') = ''
            GROUP BY pi_item.item_code
            """,
            {"item_codes": item_codes, "warehouse": warehouse},
            as_dict=True,
        )
        reserved = {r.item_code: r.qty or 0 for r in reserved_data}

    # ── Assemble response ────────────────────────────────────────────
    currency = frappe.defaults.get_defaults().get("currency", "USD")
    for item in items:
        item["rate"] = prices.get(item.item_code, 0)
        item["currency"] = currency
        actual = stock.get(item.item_code, 0)
        item["actual_qty"] = max(actual - reserved.get(item.item_code, 0), 0)
        item["barcode"] = barcodes.get(item.item_code)
        item["item_tax_template"] = tax_templates.get(item.item_code)

    return {"items": items}


def _get_group_and_children(item_group):
    """Return a list of an item group and all its descendants."""
    group_data = frappe.db.get_value("Item Group", item_group, ["lft", "rgt"])
    if not group_data:
        return [item_group]
    lft, rgt = group_data
    rows = frappe.db.sql(
        "SELECT name FROM `tabItem Group` WHERE lft >= %s AND rgt <= %s",
        (lft, rgt),
        as_list=True,
    )
    return [r[0] for r in rows]


@frappe.whitelist()
def get_item_tax_templates(company=""):
    """Get available Item Tax Templates, optionally filtered by company."""
    filters = {}
    if company:
        filters["company"] = company

    templates = frappe.get_list(
        "Item Tax Template",
        filters=filters,
        fields=["name", "company"],
        order_by="name asc",
        limit_page_length=100,
    )
    return templates


@frappe.whitelist()
def search_barcode(search_value):
    """Search for an item by barcode, serial number, or batch number."""
    # Check Item Barcode
    barcode_data = frappe.get_all(
        "Item Barcode",
        filters={"barcode": search_value},
        fields=["parent as item_code", "barcode"],
        limit=1,
    )
    if barcode_data:
        item = frappe.db.get_value("Item", barcode_data[0].item_code,
            ["item_code", "item_name", "stock_uom"], as_dict=True)
        if item:
            return {**item, "barcode": search_value}

    # Check Serial No
    if frappe.db.exists("Serial No", search_value):
        sn = frappe.db.get_value("Serial No", search_value,
            ["name", "item_code", "batch_no"], as_dict=True)
        item = frappe.db.get_value("Item", sn.item_code,
            ["item_name", "stock_uom"], as_dict=True)
        return {"item_code": sn.item_code, "item_name": item.item_name,
                "serial_no": sn.name, "batch_no": sn.batch_no,
                "uom": item.stock_uom, "barcode": search_value}

    # Check Batch
    if frappe.db.exists("Batch", search_value):
        batch = frappe.db.get_value("Batch", search_value,
            ["name", "item"], as_dict=True)
        item = frappe.db.get_value("Item", batch.item,
            ["item_name", "stock_uom"], as_dict=True)
        return {"item_code": batch.item, "item_name": item.item_name,
                "batch_no": batch.name, "uom": item.stock_uom,
                "barcode": search_value}

    return None


@frappe.whitelist()
def get_item_groups(pos_profile=""):
    """Get item groups, filtered by POS Profile if provided."""
    if pos_profile:
        profile = frappe.get_doc("POS Profile", pos_profile)
        if profile.item_groups:
            return [ig.item_group for ig in profile.item_groups]

    # Return top-level groups
    groups = frappe.get_list(
        "Item Group",
        filters={"is_group": 0},
        fields=["name"],
        order_by="name asc",
        limit_page_length=50,
    )
    return [g.name for g in groups]
