import frappe
from frappe_doc import bruno


@frappe.whitelist()
@bruno("GET")
def all(
    start: int = 0,
    limit: int = 10,
    filters: dict = None,
    fields: list = ["*"],
    order_by: str = "creation desc",
):
    try:
        docs = frappe.db.get_list(
            "Event Registration",
            filters=filters,
            limit_start=start,
            limit_page_length=limit,
            order_by=order_by,
        )
        data = [
            frappe.get_doc("Event Registration", doc.name, fields=fields)
            for doc in docs
        ]
        frappe.local.response.update(
            {
                "http_status_code": 200,
                "message": "Event Registrations fetched successfully",
                "data": data,
            }
        )
    except Exception as e:
        frappe.local.response.update({"http_status_code": 404, "error": str(e)})


@frappe.whitelist()
@bruno("GET")
def get(name: str):
    try:
        doc = frappe.get_doc("Event Registration", name)
        frappe.local.response.update(
            {
                "http_status_code": 200,
                "message": "Event Registration fetched successfully",
                "data": doc,
            }
        )
    except Exception as e:
        frappe.local.response.update({"http_status_code": 404, "error": str(e)})


@frappe.whitelist()
@bruno("POST")
def create():
    data = frappe.request.json
    try:
        doc = frappe.new_doc("Event Registration")
        doc.update(data)
        doc.insert()
        doc.submit()
        frappe.db.commit()
        frappe.local.response.update(
            {
                "http_status_code": 201,
                "message": "Event Registration created successfully",
                "data": doc,
            }
        )
    except Exception as e:
        frappe.db.rollback()
        frappe.local.response.update({"http_status_code": 400, "error": str(e)})


@frappe.whitelist()
@bruno("PUT")
def update(name: str):
    data = frappe.request.json
    try:
        doc = frappe.get_doc("Event Registration", name)
        doc.update(data)
        doc.save()
        frappe.db.commit()
        frappe.local.response.update(
            {
                "http_status_code": 200,
                "message": "Event Registration updated successfully",
                "data": doc,
            }
        )
    except Exception as e:
        frappe.db.rollback()
        frappe.local.response.update({"http_status_code": 400, "error": str(e)})


@frappe.whitelist()
@bruno("DELETE")
def delete(name: str):
    try:
        frappe.delete_doc("Event Registration", name)
        frappe.db.commit()
        frappe.local.response.update(
            {
                "http_status_code": 200,
                "message": "Event Registration deleted successfully",
            }
        )
    except Exception as e:
        frappe.local.response.update({"http_status_code": 400, "error": str(e)})


@frappe.whitelist()
@bruno("POST")
def cancel(name: str):
    try:
        doc = frappe.get_doc("Event Registration", name)
        doc.cancel()
        frappe.db.commit()
        frappe.local.response.update(
            {
                "http_status_code": 200,
                "message": "Event Registration cancelled successfully",
            }
        )
    except Exception as e:
        frappe.local.response.update({"http_status_code": 400, "error": str(e)})
