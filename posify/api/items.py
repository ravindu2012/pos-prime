import frappe


@frappe.whitelist()
def get_items(start=0, page_length=20, search_term="", item_group="", pos_profile=""):
    """Get items for POS with stock quantities and images."""
    start = int(start)
    page_length = int(page_length)

    filters = {"disabled": 0, "is_sales_item": 1, "has_variants": 0}

    if item_group:
        group_data = frappe.db.get_value("Item Group", item_group, ["lft", "rgt"])
        if not group_data:
            frappe.throw(f"Item Group '{item_group}' does not exist")
        lft, rgt = group_data
        child_groups = frappe.db.sql(
            "SELECT name FROM `tabItem Group` WHERE lft >= %s AND rgt <= %s",
            (lft, rgt),
            as_list=True,
        )
        child_groups = [g[0] for g in child_groups]
        filters["item_group"] = ["in", child_groups]

    if search_term:
        search = f"%{search_term}%"
        or_filters = {
            "item_name": ["like", search],
            "item_code": ["like", search],
            "description": ["like", search],
        }
    else:
        or_filters = {}

    # Get items
    items = frappe.get_list(
        "Item",
        filters=filters,
        or_filters=or_filters if or_filters else None,
        fields=[
            "item_code",
            "item_name",
            "description",
            "item_group",
            "stock_uom",
            "image",
            "has_batch_no",
            "has_serial_no",
            "brand",
            "weight_per_unit",
            "weight_uom",
        ],
        start=start,
        page_length=page_length,
        order_by="item_name asc",
    )

    # Get price list from POS Profile
    price_list = "Standard Selling"
    warehouse = ""
    if pos_profile:
        profile = frappe.get_doc("POS Profile", pos_profile)
        price_list = profile.selling_price_list or "Standard Selling"
        warehouse = profile.warehouse or ""

    if not items:
        return {"items": items}

    item_codes = [item.item_code for item in items]

    # Batch fetch prices
    prices = {r.item_code: r.price_list_rate for r in frappe.get_all(
        "Item Price",
        filters={"item_code": ["in", item_codes], "price_list": price_list, "selling": 1},
        fields=["item_code", "price_list_rate"],
    )}

    # Batch fetch stock
    if warehouse:
        stock = {r.item_code: r.actual_qty for r in frappe.get_all(
            "Bin",
            filters={"item_code": ["in", item_codes], "warehouse": warehouse},
            fields=["item_code", "actual_qty"],
        )}
    else:
        stock_data = frappe.db.sql(
            "SELECT item_code, SUM(actual_qty) as qty FROM `tabBin` WHERE item_code IN %s GROUP BY item_code",
            [item_codes], as_dict=True,
        )
        stock = {r.item_code: r.qty or 0 for r in stock_data}

    # Batch fetch barcodes
    barcodes = {}
    barcode_data = frappe.get_all(
        "Item Barcode",
        filters={"parent": ["in", item_codes]},
        fields=["parent", "barcode"],
        order_by="idx asc",
    )
    for b in barcode_data:
        if b.parent not in barcodes:
            barcodes[b.parent] = b.barcode

    # Batch fetch tax templates
    tax_templates = {}
    tax_data = frappe.get_all(
        "Item Tax",
        filters={"parent": ["in", item_codes]},
        fields=["parent", "item_tax_template"],
        order_by="idx asc",
    )
    for t in tax_data:
        if t.parent not in tax_templates:
            tax_templates[t.parent] = t.item_tax_template

    currency = frappe.defaults.get_defaults().get("currency", "USD")
    for item in items:
        item["rate"] = prices.get(item.item_code, 0)
        item["currency"] = currency
        item["actual_qty"] = stock.get(item.item_code, 0)
        item["barcode"] = barcodes.get(item.item_code)
        item["item_tax_template"] = tax_templates.get(item.item_code)

    return {"items": items}


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
