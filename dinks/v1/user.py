import frappe
@frappe.whitelist(allow_guest=True)
def reset_password(email):
    try:
        user = frappe.get_doc('User', email)
        return {
            "success_key": 1,
            "message": user.reset_password(send_email=True, password_expired=True)
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), ("Failed to reset password"))
        return {
            "success_key": 0,
            "error": str(e)
        }
@frappe.whitelist(allow_guest=True)
def change_password(email, old_password, new_password):
    pass
@frappe.whitelist( allow_guest=True )
def profile():
    try:
        data = frappe.local.form_dict
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        email = data.get("email")
        mobile_number = data.get("mobile_number")
        date_of_birth = data.get("birth_date")
        geder = data.get("gender")

        user = frappe.get_doc('User', frappe.session.user)
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.mobile_no = mobile_number
        user.birth_date = date_of_birth
        user.save()

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), ("Failed to update profile"))
        return {
            "success_key": 0,
            "error": str(e)
        }


