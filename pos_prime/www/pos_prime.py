import frappe


def get_context(context):
    try:
        desk_theme = frappe.db.get_value("User", frappe.session.user, "desk_theme") or "Light"
    except Exception:
        desk_theme = "Light"
    context.desk_theme = desk_theme.lower()

    # Detect desk route prefix: v16+ uses /desk/, v14-v15 use /app/
    major_version = int(frappe.__version__.split(".", 1)[0])
    context.desk_prefix = "/desk" if major_version >= 16 else "/app"
