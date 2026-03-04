app_name = "posify"
app_title = "Posify"
app_publisher = "Ravindu Gajanayaka"
app_description = "Custom POS App for ERPNext"
app_email = "ravindu@example.com"
app_license = "mit"

required_apps = ["erpnext"]

add_to_apps_screen = [
	{
		"name": "posify",
		"logo": "/assets/posify/manifest/posify-logo.svg",
		"title": "Posify",
		"route": "/posify",
	}
]

# SPA routing — serve the Vue 3 frontend for /posify/* routes
website_route_rules = [
	{"from_route": "/posify/<path:app_path>", "to_route": "posify"},
]

# Web page served at /posify
website_redirects = []

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True
