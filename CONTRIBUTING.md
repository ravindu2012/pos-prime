# Contributing to POS Prime

Thank you for your interest in contributing! This guide will help you get started.

## How to Contribute

### Reporting Bugs
1. Check [existing issues](https://github.com/ravindu2012/pos-prime/issues) to avoid duplicates
2. Open a new issue using the **Bug Report** template
3. Include steps to reproduce, ERPNext version, and screenshots

### Suggesting Features
1. Open an issue using the **Feature Request** template
2. Describe the use case and how it benefits POS workflows

### Submitting Code
1. **Fork** the repository
2. **Clone** your fork locally
3. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make your changes** following the guidelines below
5. **Test** with a running ERPNext instance
6. **Commit** with a clear message
7. **Push** to your fork and open a **Pull Request**

### Finding Issues to Work On
- Look for [`good first issue`](https://github.com/ravindu2012/pos-prime/labels/good%20first%20issue) labels
- Issues labeled [`help wanted`](https://github.com/ravindu2012/pos-prime/labels/help%20wanted) need contributors

## Development Setup

### Prerequisites
- ERPNext v14, v15, or v16 (with Frappe Bench)
- Node.js 18+
- Python 3.10+

### Installation
```bash
# In your Frappe bench directory
bench get-app https://github.com/YOUR_USERNAME/pos-prime.git
bench --site your-site.local install-app pos_prime
bench --site your-site.local migrate
```

### Frontend Development
```bash
cd apps/pos_prime/frontend
yarn install
yarn dev
```

## Code Guidelines

### Architecture
- **Backend** (`pos_prime/`) — Frappe Python app (API endpoints, hooks)
- **Frontend** (`frontend/`) — Vue 3 + TypeScript + Tailwind CSS (Vite)

### Rules
- POS Prime does NOT modify ERPNext schema — no custom fields or doctypes
- Use ERPNext standard doctypes (POS Invoice, POS Profile, Item, Customer, etc.)
- Keep the frontend fast — optimize for touch screens and barcode scanners
- Follow Vue 3 Composition API patterns
- Use TypeScript for type safety
- Test with real ERPNext data

### Commit Messages
- `Add: description` — new features
- `Fix: description` — bug fixes
- `Update: description` — improvements
- `Refactor: description` — code restructuring
- `Docs: description` — documentation

## Need Help?
- Open a [Discussion](https://github.com/ravindu2012/pos-prime/discussions) for questions
- Check the [README](README.md) for project overview
