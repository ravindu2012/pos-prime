import frappe


def get_context(context):
    desk_theme = (
        frappe.db.get_value("User", frappe.session.user, "desk_theme") or "Light"
    )
    context.desk_theme = desk_theme.lower()
