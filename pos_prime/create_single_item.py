"""Create test items. Uses auto-generated item codes from Document Naming Rule."""
import frappe


COMPANY = "Gajanayaka Enterprises - Spare Parts"
ABBR = "GE-SP"
WAREHOUSE = f"Stores - {ABBR}"
PRICE_LIST = "Standard Selling"
ITEM_GROUP = "Spare Parts"
BRAND = "Honda"
TAX_TEMPLATE = f"Sri Lanka Tax - {ABBR}"

# Auto-generated item codes from the last successful creation
ITEMS = {
	"regular": "086144",
	"service": "086129",
	"serial": "086130",
	"batch": "086131",
	"serbatch": "086132",
	"weighted": "086133",
	"taxed": "086134",
	"multiuom": "086135",
	"barcode": "086136",
	"bundle_comp_a": "086137",
	"bundle_comp_b": "086138",
	"bundle_parent": "086139",
	"zero": "086140",
	"highval": "086141",
	"frac": "086142",
	"variant_tmpl": "086143",
	"variant_s": "086147",
	"variant_m": "086148",
	"variant_l": "086149",
}


def _create_variant(size_name, abbr):
	"""Create a variant of the template."""
	if frappe.db.exists("Item", {"item_name": f"Test Variant - {size_name}"}):
		print(f"SKIP: Variant {size_name} exists")
		return
	doc = frappe.get_doc({
		"doctype": "Item",
		"item_code": f"VARIANT-{abbr}",
		"item_name": f"Test Variant - {size_name}",
		"item_group": ITEM_GROUP,
		"brand": BRAND,
		"stock_uom": "Nos",
		"is_stock_item": 1,
		"variant_of": ITEMS["variant_tmpl"],
		"attributes": [{"attribute": "Test Size", "attribute_value": size_name}],
		"item_defaults": [{"company": COMPANY, "default_warehouse": WAREHOUSE}],
	})
	doc.insert(ignore_permissions=True)
	print(f"OK: Variant {size_name} = {doc.name}")

def create_variant_s():
	_create_variant("Small", "S")

def create_variant_m():
	_create_variant("Medium", "M")

def create_variant_l():
	_create_variant("Large", "L")


def create_bundle():
	"""Create Product Bundle entry."""
	if frappe.db.exists("Product Bundle", ITEMS["bundle_parent"]):
		print("SKIP: Product Bundle exists")
		return
	frappe.get_doc({
		"doctype": "Product Bundle",
		"new_item_code": ITEMS["bundle_parent"],
		"items": [
			{"item_code": ITEMS["bundle_comp_a"], "qty": 1},
			{"item_code": ITEMS["bundle_comp_b"], "qty": 2},
		],
	}).insert(ignore_permissions=True)
	print("OK: Product Bundle created")


def create_prices():
	"""Create Item Prices for all test items."""
	prices = {
		"regular": 500,
		"service": 1000,
		"serial": 2500,
		"batch": 350,
		"serbatch": 3000,
		"weighted": 200,
		"taxed": 1500,
		"multiuom": 100,
		"barcode": 750,
		"bundle_comp_a": 300,
		"bundle_comp_b": 200,
		"bundle_parent": 450,
		"highval": 250000,
		"frac": 85,
	}
	prices["variant_s"] = 400
	prices["variant_m"] = 500
	prices["variant_l"] = 600

	for key, rate in prices.items():
		code = ITEMS.get(key)
		if not code:
			print(f"SKIP PRICE: {key} - no item code")
			continue
		if frappe.db.exists("Item Price", {"item_code": code, "price_list": PRICE_LIST}):
			print(f"SKIP PRICE: {code}")
			continue
		frappe.get_doc({
			"doctype": "Item Price",
			"item_code": code,
			"price_list": PRICE_LIST,
			"price_list_rate": rate,
			"selling": 1,
		}).insert(ignore_permissions=True)
		print(f"OK PRICE: {code} = {rate}")
	print("DONE: Prices")


def create_stock():
	"""Create stock entries for stock items."""
	stock_items = [
		("regular", 100),
		("weighted", 100),
		("taxed", 100),
		("multiuom", 100),
		("barcode", 100),
		("bundle_comp_a", 100),
		("bundle_comp_b", 100),
		("zero", 100),
		("highval", 50),
		("frac", 100),
	]
	for key, qty in stock_items:
		code = ITEMS[key]
		# Check if already has stock
		bin_qty = frappe.db.get_value("Bin", {"item_code": code, "warehouse": WAREHOUSE}, "actual_qty") or 0
		if bin_qty > 0:
			print(f"SKIP STOCK: {code} already has {bin_qty}")
			continue
		se = frappe.get_doc({
			"doctype": "Stock Entry",
			"stock_entry_type": "Material Receipt",
			"company": COMPANY,
			"items": [{"item_code": code, "qty": qty, "t_warehouse": WAREHOUSE, "basic_rate": 100}],
		})
		se.insert(ignore_permissions=True)
		se.submit()
		print(f"OK STOCK: {code} = {qty}")
	print("DONE: Stock")


def create_serial_stock():
	"""Create stock for serial number items."""
	code = ITEMS["serial"]
	bin_qty = frappe.db.get_value("Bin", {"item_code": code, "warehouse": WAREHOUSE}, "actual_qty") or 0
	if bin_qty > 0:
		print(f"SKIP: {code} already has {bin_qty}")
		return
	se = frappe.get_doc({
		"doctype": "Stock Entry",
		"stock_entry_type": "Material Receipt",
		"company": COMPANY,
		"items": [{"item_code": code, "qty": 10, "t_warehouse": WAREHOUSE, "basic_rate": 100}],
	})
	se.insert(ignore_permissions=True)
	se.submit()
	print(f"OK SERIAL STOCK: {code}")


def create_batch_stock():
	"""Create stock for batch items."""
	code = ITEMS["batch"]
	bin_qty = frappe.db.get_value("Bin", {"item_code": code, "warehouse": WAREHOUSE}, "actual_qty") or 0
	if bin_qty > 0:
		print(f"SKIP: {code} already has {bin_qty}")
		return
	se = frappe.get_doc({
		"doctype": "Stock Entry",
		"stock_entry_type": "Material Receipt",
		"company": COMPANY,
		"items": [{"item_code": code, "qty": 50, "t_warehouse": WAREHOUSE, "basic_rate": 100}],
	})
	se.insert(ignore_permissions=True)
	se.submit()
	print(f"OK BATCH STOCK: {code}")


def create_serbatch_stock():
	"""Create stock for serial+batch items."""
	code = ITEMS["serbatch"]
	bin_qty = frappe.db.get_value("Bin", {"item_code": code, "warehouse": WAREHOUSE}, "actual_qty") or 0
	if bin_qty > 0:
		print(f"SKIP: {code} already has {bin_qty}")
		return
	se = frappe.get_doc({
		"doctype": "Stock Entry",
		"stock_entry_type": "Material Receipt",
		"company": COMPANY,
		"items": [{"item_code": code, "qty": 10, "t_warehouse": WAREHOUSE, "basic_rate": 100}],
	})
	se.insert(ignore_permissions=True)
	se.submit()
	print(f"OK SERBATCH STOCK: {code}")


def create_variant_stock():
	"""Create stock for variant items."""
	for size_name in ["Small", "Medium", "Large"]:
		code = frappe.db.get_value("Item", {"item_name": f"Test Variant - {size_name}"}, "name")
		if not code:
			print(f"SKIP: Variant {size_name} not found")
			continue
		bin_qty = frappe.db.get_value("Bin", {"item_code": code, "warehouse": WAREHOUSE}, "actual_qty") or 0
		if bin_qty > 0:
			print(f"SKIP: {code} already has {bin_qty}")
			continue
		se = frappe.get_doc({
			"doctype": "Stock Entry",
			"stock_entry_type": "Material Receipt",
			"company": COMPANY,
			"items": [{"item_code": code, "qty": 30, "t_warehouse": WAREHOUSE, "basic_rate": 100}],
		})
		se.insert(ignore_permissions=True)
		se.submit()
		print(f"OK VARIANT STOCK: {code}")


def cleanup_duplicates():
	"""Delete duplicate test items (keep latest of each type)."""
	from collections import defaultdict
	items = frappe.get_all("Item",
		filters={"item_name": ["like", "Test %"]},
		fields=["name", "item_name"],
		order_by="creation asc",
	)
	# Also include Bundle Components
	items += frappe.get_all("Item",
		filters={"item_name": ["like", "Bundle Component%"]},
		fields=["name", "item_name"],
		order_by="creation asc",
	)
	groups = defaultdict(list)
	for item in items:
		groups[item.item_name].append(item.name)

	for name, codes in groups.items():
		if len(codes) > 1:
			for c in codes[:-1]:  # delete all but last
				try:
					frappe.delete_doc("Item", c, force=True, ignore_permissions=True)
					print(f"DELETED: {c} ({name})")
				except Exception as e:
					print(f"CANNOT DELETE {c}: {e}")
	# Also delete test artifacts
	for code in ["086145", "086146"]:  # Test Direct, Test Check
		if frappe.db.exists("Item", code):
			try:
				frappe.delete_doc("Item", code, force=True, ignore_permissions=True)
				print(f"DELETED: {code}")
			except Exception as e:
				print(f"CANNOT DELETE {code}: {e}")
	print("DONE: Cleanup")
