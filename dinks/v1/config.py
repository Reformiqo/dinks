import frappe
import erpnext

@frappe.whitelist()
def create_invoice(items: list, payments: list):
    try:
        if not frappe.db.exists("POS Profile", "Dink POS"):
            create_pos_profile()

        pos_profile = frappe.get_doc("POS Profile", "Dink POS")
        if not frappe.db.exists("Customer", {"email": frappe.session.user}):
            user = frappe.get_doc("User", frappe.session.user)
            name = user.full_name
            create_customer(full_name, frappe.session.user)
        
        invoice = frappe.new_doc("Sales Invoice")
        invoice.customer = frappe.db.get_value("Customer", {"email": frappe.session.user}, "name")
        invoice.company = erpnext.get_default_company()
        invoice.is_pos = 1
        invoice.pos_profile = pos_profile.name
        for item in items:
            invoice.append("items", {
                "item_code": item.get("item_code"),
                "qty": item.get("qty"),
                "rate": item.get("rate"),
            })
        for payment in payments:
            invoice.append("payments", {
                "mode_of_payment": payment.get("mode_of_payment"),
                "amount": payment.get("amount")
            })
        invoice.save()
        invoice.submit()
        frappe.db.commit()
        return invoice
    except Exception as e:
        frappe.local.response.update({
            "http_status_code": 400,
            "error": str(e)
        })
       

@frappe.whitelist()
def create_pos_profile():
    try:
        company_name = erpnext.get_default_company()
        company = frappe.get_doc("Company", company_name)
        abbr = company.abbr
        stock_settings = frappe.get_doc("Stock Settings", "Stock Settings")
        default_warehouse = stock_settings.default_warehouse
        
        pos_profile = frappe.new_doc("POS Profile")
        pos_profile.name = "Dink POS"
        pos_profile.company = company.name
        pos_profile.append("payments", {
        "mode_of_payment": "Cash",
        "default": 1
        })
        pos_profile.append("payments", {
            "mode_of_payment": "Credit Card",
        })
        pos_profile.write_off_account = company.write_off_account
        pos_profile.write_off_cost_center = company.cost_center
        pos_profile.warehouse = default_warehouse
        pos_profile.save()
        frappe.db.commit()
        return pos_profile
    except Exception as e:
        frappe.local.response.update({
            "http_status_code": 400,
            "error": str(e)
        })
@frappe.whitelist()
def create_customer(name, email):
    try:
        customer = frappe.new_doc("Customer")
        customer.customer_name = name
        customer.email = email
        customer.save()
        frappe.db.commit()
        return customer
    except Exception as e:
        frappe.local.response.update({
            "http_status_code": 400,
            "error": str(e)
        })