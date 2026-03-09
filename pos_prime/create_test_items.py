"""Create all possible inventory item types for POS testing."""
import frappe
from frappe.utils import nowdate, add_days

COMPANY = "Jayasekara Enterprises (Pvt) Ltd"
WAREHOUSE = "Stores - PE-SH"
PRICE_LIST = "Standard Selling"
CURRENCY = "LKR"
TAX_TEMPLATE = "Sri Lanka Tax - PE-SH"


def ensure_item_group(name):
    if not frappe.db.exists("Item Group", name):
        doc = frappe.get_doc({
            "doctype": "Item Group",
            "item_group_name": name,
            "parent_item_group": "Spare Parts",
        })
        doc.insert(ignore_permissions=True)
        print(f"  Created Item Group: {name}")


def add_price(item_code, rate):
    if not frappe.db.exists("Item Price", {"item_code": item_code, "price_list": PRICE_LIST}):
        frappe.get_doc({
            "doctype": "Item Price",
            "item_code": item_code,
            "price_list": PRICE_LIST,
            "price_list_rate": rate,
            "currency": CURRENCY,
        }).insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"  Price: {rate}")


def add_stock(item_code, qty, rate):
    se = frappe.get_doc({
        "doctype": "Stock Entry",
        "stock_entry_type": "Material Receipt",
        "company": COMPANY,
        "items": [{
            "item_code": item_code,
            "qty": qty,
            "t_warehouse": WAREHOUSE,
            "basic_rate": rate,
        }],
    })
    se.insert(ignore_permissions=True)
    se.submit()
    frappe.db.commit()
    print(f"  Stock: {qty} @ {rate}")


def add_stock_with_batch(item_code, qty, rate, batch_id, expiry=None):
    """Add stock for batch items using serial_and_batch_bundle (v15)."""
    batch = None
    if not frappe.db.exists("Batch", batch_id):
        batch_doc = frappe.get_doc({
            "doctype": "Batch",
            "batch_id": batch_id,
            "item": item_code,
            "expiry_date": expiry,
        })
        batch_doc.insert(ignore_permissions=True)
        print(f"  Created Batch: {batch_id}")

    # Create serial and batch bundle for v15
    bundle = frappe.get_doc({
        "doctype": "Serial and Batch Bundle",
        "item_code": item_code,
        "warehouse": WAREHOUSE,
        "company": COMPANY,
        "type_of_transaction": "Inward",
        "voucher_type": "Stock Entry",
        "entries": [{
            "batch_no": batch_id,
            "qty": qty,
        }],
    })
    bundle.insert(ignore_permissions=True)

    se = frappe.get_doc({
        "doctype": "Stock Entry",
        "stock_entry_type": "Material Receipt",
        "company": COMPANY,
        "items": [{
            "item_code": item_code,
            "qty": qty,
            "t_warehouse": WAREHOUSE,
            "basic_rate": rate,
            "serial_and_batch_bundle": bundle.name,
        }],
    })
    se.insert(ignore_permissions=True)
    se.submit()
    frappe.db.commit()
    print(f"  Stock (batch {batch_id}): {qty} @ {rate}")


def add_stock_with_serials(item_code, serial_nos, rate, batch_id=None):
    """Add stock for serial items using serial_and_batch_bundle (v15)."""
    entries = []
    for sn in serial_nos:
        entry = {"serial_no": sn, "qty": 1}
        if batch_id:
            entry["batch_no"] = batch_id
        entries.append(entry)

    bundle = frappe.get_doc({
        "doctype": "Serial and Batch Bundle",
        "item_code": item_code,
        "warehouse": WAREHOUSE,
        "company": COMPANY,
        "type_of_transaction": "Inward",
        "voucher_type": "Stock Entry",
        "entries": entries,
    })
    bundle.insert(ignore_permissions=True)

    se = frappe.get_doc({
        "doctype": "Stock Entry",
        "stock_entry_type": "Material Receipt",
        "company": COMPANY,
        "items": [{
            "item_code": item_code,
            "qty": len(serial_nos),
            "t_warehouse": WAREHOUSE,
            "basic_rate": rate,
            "serial_and_batch_bundle": bundle.name,
        }],
    })
    se.insert(ignore_permissions=True)
    se.submit()
    frappe.db.commit()
    print(f"  Stock (serials): {len(serial_nos)} @ {rate}")


def create_item(item_code, item_name, rate, **kwargs):
    if frappe.db.exists("Item", item_code):
        print(f"  SKIP {item_code} (exists)")
        return False

    group = kwargs.get("group", "Products")
    ensure_item_group(group)

    doc = frappe.get_doc({
        "doctype": "Item",
        "item_code": item_code,
        "item_name": item_name,
        "item_group": group,
        "stock_uom": kwargs.get("stock_uom", "Nos"),
        "is_stock_item": kwargs.get("is_stock", 1),
        "has_serial_no": kwargs.get("has_serial", 0),
        "has_batch_no": kwargs.get("has_batch", 0),
        "create_new_batch": kwargs.get("create_new_batch", 0),
        "is_fixed_asset": kwargs.get("is_fixed_asset", 0),
        "has_variants": kwargs.get("has_variants", 0),
        "include_item_in_manufacturing": 0,
        "brand": kwargs.get("brand", "Test Brand"),
        "valuation_rate": rate * 0.6,
    })

    if kwargs.get("weight_per_unit"):
        doc.weight_per_unit = kwargs["weight_per_unit"]
        doc.weight_uom = kwargs.get("weight_uom", "Kg")

    if kwargs.get("tax_template"):
        doc.append("taxes", {"item_tax_template": kwargs["tax_template"]})

    if kwargs.get("attributes"):
        for attr in kwargs["attributes"]:
            doc.append("attributes", {"attribute": attr})

    if kwargs.get("uoms"):
        for uom_data in kwargs["uoms"]:
            doc.append("uoms", uom_data)

    if kwargs.get("barcodes"):
        for bc in kwargs["barcodes"]:
            doc.append("barcodes", {"barcode": bc})

    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"  Created: {item_code} - {item_name}")
    return True


def run():
    # Ensure "Test Brand" exists (brand is mandatory on this site)
    if not frappe.db.exists("Brand", "Test Brand"):
        frappe.get_doc({"doctype": "Brand", "brand": "Test Brand"}).insert(ignore_permissions=True)
        print("Created Brand: Test Brand")

    # ============================================================
    # 1. Regular Stock Item
    # ============================================================
    print("\n1. REGULAR STOCK ITEM")
    if create_item("TEST-REGULAR-001", "Test Regular Item", 500):
        add_price("TEST-REGULAR-001", 500)
        add_stock("TEST-REGULAR-001", 100, 300)

    # ============================================================
    # 2. Non-Stock / Service Item
    # ============================================================
    print("\n2. NON-STOCK SERVICE ITEM")
    if create_item("TEST-SERVICE-001", "Test Service (Labour)", 1000, is_stock=0, group="Services"):
        add_price("TEST-SERVICE-001", 1000)

    # ============================================================
    # 3. Serial Number Item
    # ============================================================
    print("\n3. SERIAL NUMBER ITEM")
    if create_item("TEST-SERIAL-001", "Test Serial Item (Phone)", 25000, has_serial=1):
        add_price("TEST-SERIAL-001", 25000)
        serials = [f"SN-PHONE-{str(i).zfill(3)}" for i in range(1, 11)]
        add_stock_with_serials("TEST-SERIAL-001", serials, 15000)

    # ============================================================
    # 4. Batch Number Item
    # ============================================================
    print("\n4. BATCH NUMBER ITEM")
    if create_item("TEST-BATCH-001", "Test Batch Item (Oil)", 750, has_batch=1, create_new_batch=1):
        add_price("TEST-BATCH-001", 750)
        add_stock_with_batch("TEST-BATCH-001", 50, 400, "BATCH-OIL-2026-A",
                             expiry=add_days(nowdate(), 365))
        add_stock_with_batch("TEST-BATCH-001", 30, 420, "BATCH-OIL-2026-B",
                             expiry=add_days(nowdate(), 180))

    # ============================================================
    # 5. Serial + Batch Item
    # ============================================================
    print("\n5. SERIAL + BATCH ITEM")
    if create_item("TEST-SERBATCH-001", "Test Serial+Batch (Battery)", 8000,
                    has_serial=1, has_batch=1, create_new_batch=1):
        add_price("TEST-SERBATCH-001", 8000)
        # Create batch first
        batch_id = "BATCH-BATT-2026-A"
        if not frappe.db.exists("Batch", batch_id):
            frappe.get_doc({
                "doctype": "Batch",
                "batch_id": batch_id,
                "item": "TEST-SERBATCH-001",
                "expiry_date": add_days(nowdate(), 730),
            }).insert(ignore_permissions=True)
        serials = [f"SN-BATT-{str(i).zfill(3)}" for i in range(1, 6)]
        add_stock_with_serials("TEST-SERBATCH-001", serials, 5000, batch_id=batch_id)

    # ============================================================
    # 6. Weighted Item
    # ============================================================
    print("\n6. WEIGHTED ITEM")
    if create_item("TEST-WEIGHT-001", "Test Heavy Part (2.5kg)", 1200,
                    weight_per_unit=2.5, weight_uom="Kg"):
        add_price("TEST-WEIGHT-001", 1200)
        add_stock("TEST-WEIGHT-001", 50, 700)

    # ============================================================
    # 7. Item with Tax Template
    # ============================================================
    print("\n7. ITEM WITH TAX TEMPLATE")
    if create_item("TEST-TAXED-001", "Test Taxed Item", 2000, tax_template=TAX_TEMPLATE):
        add_price("TEST-TAXED-001", 2000)
        add_stock("TEST-TAXED-001", 80, 1200)

    # ============================================================
    # 8. Item with Multiple UOMs
    # ============================================================
    print("\n8. MULTI-UOM ITEM")
    if create_item("TEST-MULTIUOM-001", "Test Multi-UOM (Bolts)", 50,
                    stock_uom="Nos",
                    uoms=[
                        {"uom": "Box", "conversion_factor": 12},
                        {"uom": "Kg", "conversion_factor": 100},
                    ]):
        add_price("TEST-MULTIUOM-001", 50)
        add_stock("TEST-MULTIUOM-001", 500, 25)

    # ============================================================
    # 9. Item with Barcode
    # ============================================================
    print("\n9. BARCODE ITEM")
    if create_item("TEST-BARCODE-001", "Test Barcode Item", 350,
                    barcodes=["4006381333931", "8901234567890"]):
        add_price("TEST-BARCODE-001", 350)
        add_stock("TEST-BARCODE-001", 200, 180)

    # ============================================================
    # 10. Item Variant (Template + Variants)
    # ============================================================
    print("\n10. ITEM VARIANT (Template)")
    # Ensure attributes exist
    for attr_name, values in [("Size", ["S", "M", "L", "XL"]), ("Colour", ["Red", "Blue", "Black"])]:
        if not frappe.db.exists("Item Attribute", attr_name):
            attr = frappe.get_doc({
                "doctype": "Item Attribute",
                "attribute_name": attr_name,
                "item_attribute_values": [{"attribute_value": v, "abbr": v[:2].upper()} for v in values],
            })
            attr.insert(ignore_permissions=True)
            print(f"  Created Attribute: {attr_name}")

    if create_item("TEST-VARIANT-TMPL", "Test T-Shirt (Template)", 0,
                    has_variants=1, attributes=["Size", "Colour"]):
        # Create a few variants
        variants = [
            ("TEST-VARIANT-TMPL-S-RE", "Test T-Shirt - S Red", {"Size": "S", "Colour": "Red"}),
            ("TEST-VARIANT-TMPL-M-BL", "Test T-Shirt - M Blue", {"Size": "M", "Colour": "Blue"}),
            ("TEST-VARIANT-TMPL-L-BK", "Test T-Shirt - L Black", {"Size": "L", "Colour": "Black"}),
        ]
        for v_code, v_name, attrs in variants:
            if not frappe.db.exists("Item", v_code):
                v_doc = frappe.get_doc({
                    "doctype": "Item",
                    "item_code": v_code,
                    "item_name": v_name,
                    "item_group": "Products",
                    "stock_uom": "Nos",
                    "variant_of": "TEST-VARIANT-TMPL",
                    "attributes": [{"attribute": k, "attribute_value": v} for k, v in attrs.items()],
                })
                v_doc.insert(ignore_permissions=True)
                add_price(v_code, 1500)
                add_stock(v_code, 30, 800)
                print(f"  Variant: {v_code}")

    # ============================================================
    # 11. Product Bundle (non-stock parent + stock components)
    # ============================================================
    print("\n11. PRODUCT BUNDLE")
    if create_item("TEST-BUNDLE-001", "Test Combo Pack", 2500, is_stock=0):
        add_price("TEST-BUNDLE-001", 2500)
        if not frappe.db.exists("Product Bundle", {"new_item_code": "TEST-BUNDLE-001"}):
            bundle = frappe.get_doc({
                "doctype": "Product Bundle",
                "new_item_code": "TEST-BUNDLE-001",
                "items": [
                    {"item_code": "TEST-REGULAR-001", "qty": 2, "description": "Regular Item x2"},
                    {"item_code": "TEST-WEIGHT-001", "qty": 1, "description": "Heavy Part x1"},
                ],
            })
            bundle.insert(ignore_permissions=True)
            print("  Created Product Bundle: TEST-BUNDLE-001")

    # ============================================================
    # 12. Fixed Asset Item
    # ============================================================
    print("\n12. FIXED ASSET ITEM")
    # Ensure asset category
    if not frappe.db.exists("Asset Category", "Test Equipment"):
        frappe.get_doc({
            "doctype": "Asset Category",
            "asset_category_name": "Test Equipment",
            "enable_cwip_accounting": 0,
            "finance_book_detail": [{
                "depreciation_method": "Straight Line",
                "total_number_of_depreciations": 36,
                "frequency_of_depreciation": 12,
            }],
        }).insert(ignore_permissions=True)
        print("  Created Asset Category: Test Equipment")

    if create_item("TEST-ASSET-001", "Test Fixed Asset (Laptop)", 150000,
                    is_stock=0, is_fixed_asset=1, group="Fixed Asset"):
        add_price("TEST-ASSET-001", 150000)

    # ============================================================
    # 13. Zero-rate / Free Item
    # ============================================================
    print("\n13. ZERO-RATE FREE ITEM")
    if create_item("TEST-FREE-001", "Test Free Sample", 0):
        add_price("TEST-FREE-001", 0)
        add_stock("TEST-FREE-001", 100, 0)

    # ============================================================
    # 14. Very Expensive Item (test large amounts)
    # ============================================================
    print("\n14. HIGH-VALUE ITEM")
    if create_item("TEST-EXPENSIVE-001", "Test Expensive Item", 999999.99):
        add_price("TEST-EXPENSIVE-001", 999999.99)
        add_stock("TEST-EXPENSIVE-001", 5, 600000)

    # ============================================================
    # 15. Fractional Qty Item (sold by weight/length)
    # ============================================================
    print("\n15. FRACTIONAL QTY ITEM (by Meter)")
    if create_item("TEST-METER-001", "Test Cable (per meter)", 120, stock_uom="Meter"):
        add_price("TEST-METER-001", 120)
        add_stock("TEST-METER-001", 500, 60)

    frappe.db.commit()
    print("\n" + "=" * 60)
    print("ALL TEST ITEMS CREATED SUCCESSFULLY")
    print("=" * 60)

    # Summary
    print("\nItem Summary:")
    test_items = frappe.get_all("Item",
        filters={"item_code": ["like", "TEST-%"]},
        fields=["item_code", "item_name", "has_serial_no", "has_batch_no",
                "is_stock_item", "is_fixed_asset", "has_variants", "stock_uom"],
        order_by="item_code")
    for i in test_items:
        flags = []
        if i.has_serial_no: flags.append("SERIAL")
        if i.has_batch_no: flags.append("BATCH")
        if not i.is_stock_item and not i.is_fixed_asset: flags.append("NON-STOCK")
        if i.is_fixed_asset: flags.append("ASSET")
        if i.has_variants: flags.append("TEMPLATE")
        if "VARIANT-TMPL-" in i.item_code: flags.append("VARIANT")
        flag_str = " [" + ", ".join(flags) + "]" if flags else ""
        print(f"  {i.item_code:30s} {i.item_name:40s} UOM={i.stock_uom}{flag_str}")


if __name__ == "__main__":
    run()
