import frappe
from frappe import _

def validate_request_params(allowed_params):
    """
    Validates incoming request parameters against the allowed list.
    Automatically allows 'cmd' (default in Frappe).
    
    :param allowed_params: Set of allowed parameter names
    """
    allowed = set(allowed_params) | {"cmd"}
    incoming_params = set(frappe.form_dict.keys())
    extra_params = incoming_params - allowed

    if extra_params:
        frappe.local.response.update({
            "http_status_code": 400,
            "error": _("Invalid parameters: {0}").format(", ".join(extra_params))
        })
        frappe.throw(_("Invalid parameters: {0}").format(", ".join(extra_params)))
