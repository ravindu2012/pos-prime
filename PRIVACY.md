# Privacy Policy

**POS Prime** — A modern Point of Sale for ERPNext

*Last updated: March 6, 2026*

## Overview

POS Prime is a self-hosted application that runs entirely on your own ERPNext/Frappe instance. We do not operate any external servers, cloud services, or data collection infrastructure.

## Data Collection

POS Prime does **not** collect, store, transmit, or share any data with third parties. All data processed by POS Prime — including customer information, invoices, payment records, and inventory data — resides exclusively on your self-hosted ERPNext instance.

Specifically, POS Prime:

- Does **not** send data to any external server
- Does **not** use analytics, tracking, or telemetry
- Does **not** use cookies beyond those required by the Frappe framework for session management
- Does **not** collect personal information of end users
- Does **not** integrate with any third-party data services

## Data Storage

All data is stored in your ERPNext database using standard ERPNext doctypes (POS Invoice, POS Opening Entry, Customer, Item, etc.). POS Prime does not create any custom doctypes or store data outside of ERPNext's standard schema.

You retain full ownership and control of all your data.

## Data Processing

POS Prime processes data only within your browser and your ERPNext server:

- **Browser**: Renders the POS interface, manages cart state, and communicates with your ERPNext server via authenticated API calls
- **Server**: Processes transactions using ERPNext's standard APIs and business logic

No data leaves your infrastructure.

## Third-Party Services

POS Prime does not integrate with or send data to any third-party services. Payment processing is handled entirely through your configured ERPNext payment methods.

## Security

POS Prime inherits the security model of the Frappe framework:

- All API calls require authenticated sessions
- Role-based access control via ERPNext's permission system
- No additional authentication mechanisms or external credentials are stored

## Children's Privacy

POS Prime does not knowingly collect any personal information from children.

## Changes to This Policy

Updates to this privacy policy will be reflected in this document within the repository. The "Last updated" date at the top indicates the most recent revision.

## Contact

For privacy-related questions or concerns:

- GitHub Issues: [github.com/ravindu2012/pos-prime/issues](https://github.com/ravindu2012/pos-prime/issues)
- GitHub Discussions: [github.com/ravindu2012/pos-prime/discussions](https://github.com/ravindu2012/pos-prime/discussions)
