# POS Prime vs ERPNext Built-in POS: Item Type Comparison Report

**Date:** 2026-03-08
**ERPNext Version:** v15 | **POS Prime Version:** 0.0.1

## Test Items Created

| Code | Item Name | Type | UOM | Price (LKR) | Stock |
|------|-----------|------|-----|-------------|-------|
| 086144 | Test Regular Item | Stock | Nos | 500 | 100 |
| 086129 | Test Service Item | Non-Stock | Nos | 1,000 | - |
| 086130 | Test Serial Item | Serial No | Nos | 2,500 | 10 |
| 086131 | Test Batch Item | Batch | Nos | 350 | 50 |
| 086132 | Test Serial+Batch Item | Serial+Batch | Nos | 3,000 | 10 |
| 086133 | Test Weighted Item | Weighted | Kg | 200 | 100 |
| 086134 | Test Taxed Item | Tax Template | Nos | 1,500 | 100 |
| 086135 | Test Multi-UOM Item | Multi-UOM | Nos (Box=12) | 100 | 100 |
| 086136 | Test Barcode Item | Barcode (EAN) | Nos | 750 | 100 |
| 086143 | Test Variant Template | Template | Nos | - | - |
| 086147 | Test Variant - Small | Variant | Nos | 400 | 30 |
| 086148 | Test Variant - Medium | Variant | Nos | 500 | 30 |
| 086149 | Test Variant - Large | Variant | Nos | 600 | 30 |
| 086139 | Test Product Bundle | Bundle (A x1, B x2) | Nos | 450 | - |
| 086137 | Bundle Component A | Stock | Nos | 300 | 100 |
| 086138 | Bundle Component B | Stock | Nos | 200 | 100 |
| 086140 | Test Zero Rate Item | Zero Price | Nos | 0 | 100 |
| 086141 | Test High Value Item | High Value | Nos | 250,000 | 50 |
| 086142 | Test Fractional Qty Item | Fractional | Meter | 85 | 100 |

---

## Comparison Summary

| # | Item Type | POS Prime | ERPNext POS | Winner |
|---|-----------|-----------|-------------|--------|
| 1 | Regular Stock | Full | Full | Tie |
| 2 | Non-Stock/Service | Full | Full | Tie |
| 3 | Serialized | Full (auto-fetch FIFO, dialog) | Full (auto-fetch, textarea) | Tie |
| 4 | Batch | Full (expiry dates shown) | Full (batch dropdown) | POS Prime (expiry visibility) |
| 5 | Serial+Batch | Full (two-step dialog) | Full (auto-clone rows) | ERPNext (auto-cloning) |
| 6 | Weighted | Partial (manual qty) | Partial (manual qty) | Tie |
| 7 | Taxed (Item Tax) | Full (server-side calc) | Full (standard calc) | Tie |
| 8 | Multi-UOM | Full (UOM selector) | Full (UOM dropdown) | Tie |
| 9 | Barcode | Full (HID + camera scan) | Full (onscan.js HID) | POS Prime (camera scan) |
| 10 | Variant Template | Hidden (correct) | Hidden (correct) | Tie |
| 10b | Variant Items | Shown & sellable | Shown & sellable | Tie |
| 11 | Product Bundle | Full (badge + stock calc) | Partial (submit-only validation) | POS Prime |
| 12 | Fixed Asset | Shown (treated as regular) | Hidden (excluded) | ERPNext (correct exclusion) |
| 13 | Zero-Rate | Allowed (no restriction) | Blocked (price > 0 required) | Depends on use case |
| 14 | High-Value | No warnings | No warnings | Tie |
| 15 | Fractional Qty | Full (decimal numpad) | Full (decimal input) | Tie |

---

## Detailed Comparison

### 1. Regular Stock Item
| Aspect | POS Prime | ERPNext POS |
|--------|-----------|-------------|
| Display | Item card with image | Item card with image |
| Stock indicator | Color-coded badge (green >10, amber >0, red =0) | Color-coded pill (green/orange/red) |
| Add to cart | Single click | Single click |
| Stock validation | Real-time on add | Real-time on add |
| **Verdict** | **Equivalent** | **Equivalent** |

### 2. Non-Stock / Service Item
| Aspect | POS Prime | ERPNext POS |
|--------|-----------|-------------|
| Display | Shown, no stock badge | Shown, no stock indicator |
| Stock validation | Skipped (`is_stock_item=0` bypass) | Skipped |
| **Verdict** | **Equivalent** | **Equivalent** |

### 3. Serialized Item
| Aspect | POS Prime | ERPNext POS |
|--------|-----------|-------------|
| Selection UI | BatchSerialSelector dialog | Item details form with textarea |
| Auto-fetch | FIFO order from warehouse | Auto-fetch button available |
| Manual entry | Supported | Supported |
| Cart display | "SN: ABC123" badge | Serial number in item details |
| Validation | Frontend + backend | Backend at submit |
| **Verdict** | **POS Prime** (better UX with dialog) | Functional but less intuitive |

### 4. Batch Item
| Aspect | POS Prime | ERPNext POS |
|--------|-----------|-------------|
| Selection UI | BatchSerialSelector dialog with expiry dates | Batch dropdown in item details |
| Expiry filtering | Server-side, non-expired only | Server-side filtered |
| Expiry display | Shown per batch in dialog | Not prominently displayed |
| Qty per batch | Shown in selection dialog | Available via dropdown |
| **Verdict** | **POS Prime** (expiry date visibility) | Functional |

### 5. Serial + Batch Item
| Aspect | POS Prime | ERPNext POS |
|--------|-----------|-------------|
| Selection flow | Two-step: batch first, then serial | Serial first, auto-batch assignment |
| Multi-batch handling | Separate cart lines per batch | Auto-clones cart rows per batch |
| UX complexity | Manual batch+serial selection | Auto-assigns batch from serial selection |
| **Verdict** | Functional | **ERPNext** (smart auto-cloning) |

### 6. Weighted Item
| Aspect | POS Prime | ERPNext POS |
|--------|-----------|-------------|
| Weight input | No dedicated widget | No dedicated widget |
| UOM support | UOM selector if multi-UOM configured | UOM selector |
| Weight tracking | `weight_per_unit` and `weight_uom` stored | Weight fields read-only |
| **Verdict** | **Equivalent** (both limited) | **Equivalent** |

### 7. Taxed Item (Item Tax Template)
| Aspect | POS Prime | ERPNext POS |
|--------|-----------|-------------|
| Tax template | Fetched and applied on cart add | Applied via POS Profile item details |
| Tax calculation | Server-side via `calculate_taxes()` API | Standard POS Invoice tax calc |
| Tax display | Individual tax rows in cart summary | Tax in grand total section |
| Cart display | Tax template label on cart item | Not shown on cart item |
| **Verdict** | **POS Prime** (tax template visible in cart) | Functional |

### 8. Multi-UOM Item
| Aspect | POS Prime | ERPNext POS |
|--------|-----------|-------------|
| UOM selector | Dropdown if >1 UOM | Dropdown in item details |
| Conversion factor | Auto-applied | Auto-fetched |
| Price adjustment | Based on conversion factor | Based on conversion factor |
| **Verdict** | **Equivalent** | **Equivalent** |

### 9. Barcode Item
| Aspect | POS Prime | ERPNext POS |
|--------|-----------|-------------|
| HID scanner | Supported via `useBarcodeScanner` composable | Supported via `onscan.js` library |
| Camera scanning | Supported (CameraScanner component) | Not available |
| Barcode + UOM | First barcode used | Barcode-specific UOM auto-selected |
| Fuzzy search | Barcode included in Fuse.js index | Direct barcode match only |
| Auto-add | Item added on scan | Item added on scan |
| **Verdict** | **POS Prime** (camera scanning + fuzzy search) | **ERPNext** (barcode-UOM mapping) |

### 10. Variant Template + Variants
| Aspect | POS Prime | ERPNext POS |
|--------|-----------|-------------|
| Template shown | No (`has_variants=0` filter) | No (`has_variants=0` filter) |
| Variant items shown | Yes (as individual items) | Yes (as individual items) |
| Attribute selection UI | None | None |
| **Verdict** | **Equivalent** (both lack template selection UI) | **Equivalent** |

Note: Neither POS supports selecting variants from a template. Both show individual variant items as separate sellable items in the grid. This is actually the correct behavior for POS — templates are not sellable.

### 11. Product Bundle
| Aspect | POS Prime | ERPNext POS |
|--------|-----------|-------------|
| Display | "Bundle" badge on item card | No visual distinction |
| Stock availability | Calculated from component stock (upfront) | Validated only at invoice submit |
| Component expansion | Not shown in cart | Not shown in cart |
| Stock validation timing | On add to cart (pre-check) | On submit (post-check) |
| **Verdict** | **POS Prime** (bundle badge + upfront stock calc) | Late validation = poor UX |

### 12. Fixed Asset Item
| Aspect | POS Prime | ERPNext POS |
|--------|-----------|-------------|
| Display | Shown (treated as regular item) | Hidden (`is_fixed_asset=0` filter) |
| Handling | No special logic | Correctly excluded |
| **Verdict** | **ERPNext** (correct exclusion) | POS Prime should filter these |

### 13. Zero-Rate Item
| Aspect | POS Prime | ERPNext POS |
|--------|-----------|-------------|
| Display | Shown with "0.00" price | Shown but blocked |
| Add to cart | Allowed | Blocked (orange warning: "Price is not set") |
| Use cases | Free samples, promotional items | Not supported in POS |
| **Verdict** | **POS Prime** (allows free/promo items) | Too restrictive |

### 14. High-Value Item
| Aspect | POS Prime | ERPNext POS |
|--------|-----------|-------------|
| Display | Normal | Normal |
| Confirmation | No special dialog | No special dialog |
| **Verdict** | **Equivalent** (both lack high-value warnings) | **Equivalent** |

### 15. Fractional Qty Item
| Aspect | POS Prime | ERPNext POS |
|--------|-----------|-------------|
| Decimal input | NumPad with `step="any"` | Standard numeric field |
| Precision | Rounded to 2 decimal places | Standard Frappe precision |
| **Verdict** | **Equivalent** | **Equivalent** |

---

## Feature Matrix

| Feature | POS Prime | ERPNext POS |
|---------|:---------:|:-----------:|
| Regular items | Yes | Yes |
| Non-stock items | Yes | Yes |
| Serial number selection | Dialog | Textarea |
| Serial auto-fetch (FIFO) | Yes | Yes |
| Batch selection | Dialog with expiry | Dropdown |
| Serial+Batch auto-clone | No | Yes |
| Weight input widget | No | No |
| Item Tax Template | Yes (visible in cart) | Yes |
| Multi-UOM selector | Yes | Yes |
| Barcode HID scanner | Yes | Yes |
| Barcode camera scan | Yes | No |
| Barcode-specific UOM | No (first barcode) | Yes |
| Variant template selection | No | No |
| Variant items (as individual) | Yes | Yes |
| Product Bundle badge | Yes | No |
| Bundle stock pre-check | Yes (on add) | No (on submit) |
| Fixed asset exclusion | No (shown) | Yes (excluded) |
| Zero-rate items | Allowed | Blocked |
| High-value warnings | No | No |
| Fractional quantities | Yes | Yes |
| Fuzzy search (typos) | Yes (Fuse.js) | No (exact match) |
| Virtual scroll (large catalogs) | Yes (@tanstack) | No |
| Pricing rule badges | Yes | No |
| Store credit | Yes | No |
| Loyalty points | Yes | Yes |
| Resizable cart | Yes | No |
| Keyboard shortcuts (F-keys) | Yes | Partial |
| Dark mode | Yes | No |
| Customer pole display | Yes | No |
| Self-checkout kiosk | Yes | No |
| RTL support | Yes | No |

---

## Recommendations for POS Prime

Based on this comparison, the following improvements could be made:

1. **Filter Fixed Asset items** - Add `is_fixed_asset=0` to item query (matches ERPNext behavior)
2. **Serial+Batch auto-cloning** - When serials from multiple batches are selected, auto-split into separate cart lines
3. **Barcode-specific UOM** - When scanning a barcode that has a specific UOM defined, auto-select that UOM
4. **Weight input widget** - Add dedicated weight input for items sold by weight (neither POS has this)
5. **High-value confirmation** - Optional confirmation dialog for items above a threshold

## Overall Assessment

**POS Prime wins on:** Bundle handling, barcode scanning (camera), UI polish (badges, fuzzy search, dark mode, virtual scroll), zero-rate item support, store credit, customer display, kiosk mode

**ERPNext POS wins on:** Serial+batch auto-cloning, barcode-UOM mapping, fixed asset exclusion

**Tied on:** Regular items, non-stock, weighted, taxed, multi-UOM, variants, high-value, fractional qty

POS Prime handles **14 of 15** item types correctly (fixed asset being the exception where it should filter but doesn't). ERPNext POS handles **13 of 15** correctly (zero-rate items blocked, no bundle pre-validation).
