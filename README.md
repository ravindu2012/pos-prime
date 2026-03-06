<div align="center">

# Posify

**A modern, fast Point of Sale for ERPNext**

Built for speed, touch screens, and real retail workflows.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Frappe](https://img.shields.io/badge/Frappe-v14%20|%20v15%20|%20v16-blue)](https://frappeframework.com)

</div>

---

## Why Posify?

ERPNext's built-in POS is functional but limited. Posify is a complete replacement built from the ground up with Vue 3, designed for businesses that need a fast, reliable, and modern point of sale.

- **Instant item search** with barcode scanning and manual lookup
- **Real-time stock validation** so you never sell what you don't have
- **Self-checkout kiosk mode** for customer-facing touchscreens
- **Customer pole display** support (screen-based and VFD serial)
- **Works with ERPNext's inventory, taxes, and accounting** - no separate system

---

## Zero Modifications to ERPNext

Posify does **not** add custom fields, custom doctypes, or modify any existing ERPNext schema. It works entirely with ERPNext's standard doctypes:

- **POS Profile** - your existing POS configuration
- **POS Opening Entry** - standard shift management
- **POS Invoice** - native ERPNext invoices, fully compatible with consolidation and accounting
- **Item, Customer, Item Price, Bin** - reads directly from your existing data
- **Item Tax Template, Sales Taxes and Charges** - uses your existing tax setup

**Why this matters:**
- Upgrade ERPNext freely - Posify will never block or break your upgrades
- Uninstall cleanly - remove Posify and nothing changes in your ERPNext data
- No data lock-in - every invoice Posify creates is a standard POS Invoice, visible in Desk and reports
- Works alongside ERPNext's built-in POS - use both if you want

---

## Screenshots

### POS - Item Grid & Cart
Browse items by category, search by name or barcode, and build the cart with a single tap.

![POS Item Grid](screenshots/pos-item-grid.png)

### POS - Cart with Items
Full cart sidebar with quantity controls, discounts, coupon codes, and real-time totals.

![POS Cart](screenshots/pos-cart.png)

### POS - Payment
Multiple payment methods - Cash, Credit Card, Bank Draft, Cheque. Split payments supported.

![POS Payment](screenshots/pos-payment.png)

### POS - Payment Success
Invoice receipt with print option after successful payment.

![POS Payment Success](screenshots/pos-payment-success.png)

### POS - Past Orders
View, search, and manage all past invoices. Filter by status - All, Paid, Return, Draft.

![POS Orders](screenshots/pos-orders.png)

### POS - Returns
Process returns directly from the POS with item search, quantity adjustment, and refund method selection.

![POS Returns](screenshots/pos-returns.png)

### POS - Customer 360
Complete customer profile with contact info, loyalty points, and recent invoice history.

![Customer 360](screenshots/pos-customer-360.png)

### Customer Pole Display
Dedicated customer-facing display showing live cart items and totals. Supports both screen-based and VFD serial displays.

![Customer Pole Display](screenshots/customer-pole-display.png)

### Customer Display - Welcome Screen
Customer display with phone number entry for loyalty point lookup.

![Customer Display Welcome](screenshots/customer-display-welcome.png)

---

## Features

### Point of Sale
- Item grid with images, categories, and stock indicators
- Barcode scanner support (USB/Bluetooth HID scanners)
- Cart with inline quantity, discount, and price controls
- Multiple payment methods (Cash, Card, Bank Draft, Cheque)
- Split payments across multiple methods
- Coupon code support
- Invoice-level and item-level discounts
- Tax calculation with Item Tax Templates
- POS returns and refunds
- Order history with search and filters
- Print and reprint invoices
- Hold and resume orders

### Self-Checkout Kiosk
- Fullscreen kiosk mode for dedicated touchscreens
- Barcode scanning + manual item code entry
- Phone number lookup for customer loyalty
- Card and cash payment flows
- Auto-reset after transaction completes
- Idle timeout returns to welcome screen
- Navigation prevention (no accidental exits)

### Customer Display
- Real-time cart mirroring on a second screen
- Company branding with logo
- Phone number entry for loyalty points
- VFD serial display support
- Multi-session broadcast

### Customer 360
- Customer profile with contact details
- Loyalty points balance
- Recent POS invoice history
- Quick customer search

---

## Compatibility

| ERPNext Version | Frappe Version | Status |
|----------------|---------------|--------|
| v14 | v14 | Supported |
| v15 | v15 | Supported |
| v16 | v16 | Supported |

---

## Installation

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/ravindu2012/posify --branch main
bench --site your-site.localhost install-app posify
```

After installation, navigate to `/posify` on your site to open the POS.

### Kiosk Mode

1. Open a POS session in Posify
2. Navigate to `/posify/kiosk` on your touchscreen device
3. The kiosk auto-detects the open session

### Customer Display

1. Open a POS session in Posify
2. Click the **Customer Display** panel in the sidebar
3. Open the display URL on your second screen

---

## Tech Stack

- **Frontend**: Vue 3 + TypeScript + Pinia + Tailwind CSS
- **UI Framework**: frappe-ui
- **Backend**: Frappe Framework + ERPNext
- **Build**: Vite

---

## Contributing

This app uses `pre-commit` for code formatting and linting:

```bash
cd apps/posify
pre-commit install
```

Tools used: ruff, eslint, prettier, pyupgrade

---

## License

GPL v3 - see [license.txt](license.txt)

---

<div align="center">

**A [Raveforge](https://github.com/ravindu2012) Product**

</div>
