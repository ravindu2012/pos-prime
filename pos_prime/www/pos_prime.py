import frappe


def get_context(context):
    try:
        desk_theme = frappe.db.get_value("User", frappe.session.user, "desk_theme") or "Light"
    except Exception:
        desk_theme = "Light"
    context.desk_theme = desk_theme.lower()
