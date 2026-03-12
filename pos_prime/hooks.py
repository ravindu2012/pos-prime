# Copyright (c) 2026, Ravindu Gajanayaka
# Licensed under GPLv3. See license.txt

app_name = "pos_prime"
app_title = "POS Prime"
app_publisher = "Ravindu Gajanayaka"
app_description = "Custom POS App for ERPNext"
app_email = "ravindu@example.com"
app_license = "mit"

required_apps = ["erpnext"]

app_include_js = "/assets/pos_prime/js/pos_prime.js"

add_to_apps_screen = [
	{
		"name": "pos_prime",
		"logo": "/assets/pos_prime/manifest/pos-prime-logo.png",
		"title": "POS Prime",
		"route": "/app/pos-terminal",  # Frappe resolves this; v16 uses /desk/ automatically
	}
]

# SPA routing — serve the Vue 3 frontend for /pos-prime/* routes
website_route_rules = [
	{"from_route": "/pos-prime/<path:app_path>", "to_route": "pos_prime"},
	{"from_route": "/pos-prime", "to_route": "pos_prime"},
]

# Web page served at /pos-prime
website_redirects = []

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True
