import frappe
from datetime import datetime, timedelta
from frappe.utils import getdate, cint, today, flt
import razorpay
import frappe
from datetime import datetime, timedelta
import json

@frappe.whitelist(allow_guest=True)
def get_member_payment_link():
    form_data = frappe.local.form_dict
    first_name = form_data.get("first_name")
    last_name = form_data.get("last_name")
    phone  = form_data.get("phone")
    email = form_data.get("email")
    amount = form_data.get("amount")
    full_name = f"{first_name} {last_name}"

    settings = frappe.get_doc("Razorpay Settings")
    id = settings.api_key
    secret = settings.get_password("api_secret")
    client = razorpay.Client(auth=(id, secret))

    data = {
        "type": "link",
        "amount": cint(frappe.db.get_value("Item Price", {"item_code": "Dink Patron Membership", "price_list": "Standard Selling"}, "price_list_rate")) * 100,
        "currency": "INR",
        "description": full_name,
        "callback_url": "https://dinksports.erpera.io/buy/become-a-member/confirmation",
        "callback_method": "get"
    }
    response = client.invoice.create(data)
    return response.get('short_url')


@frappe.whitelist(allow_guest=True)
def register_member():
    import erpnext
    form_data = frappe.local.form_dict
    first_name = form_data.get("first_name")
    last_name = form_data.get("last_name")
    phone  = form_data.get("phone")
    email = form_data.get("email")
    if not frappe.db.exists("Customer", {"phone": phone}):
        customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": f"{first_name} {last_name}",
            "phone": phone,
            "email": email
        })
        customer.save(ignore_permissions=True)
        frappe.db.commit()
    else:
        customer = frappe.get_doc("Customer", {"phone": phone})

    subscription = frappe.new_doc("Subscription")
    subscription.party_type = "Customer"
    subscription.party = customer.name
    subscription.start_date = today()
    subscription.company = erpnext.get_default_company()
    subscriptiongenerate_invoice_at = "Beginning of the current subscription period"
    subscription.append("plans", {
        "plan": "Dink Patron Membership",
        "qty": 1,
    })
    subscription.save(ignore_permissions=True)
    frappe.db.commit()
    return {"subscription":subscription.name, "customer": customer.name}


@frappe.whitelist(allow_guest=True)
def get_member(name):
    customer = frappe.get_doc("Customer", {"name": name})

    return {
        "customer_name": customer.name,
        "subscription": frappe.db.get_value("Subscription", {"party": customer.name}, "name")
    }
@frappe.whitelist(allow_guest=True)
def get_booking():
    form_data = frappe.local.form_dict
    name = form_data.get('name')
    booking = frappe.get_doc("Booking", {"name": name})
    slots = []
    for slot in booking.slots:
        slots.append({
            "time": slot.time
        })
    location = frappe.get_doc("Location Courts", booking.court)

    return {
        "name": booking.name,
        'player': booking.players,
        "location": frappe.db.get_value("Court", location.court, "location"),
        "court_number": frappe.db.get_value("Location Courts", booking.court, "court_number"),
        "customer": booking.customer,
        "date": booking.date,
        "pay_at_court": booking.pay_at_court,
        "time_period": booking.time_period,
        "slots": slots
    }


@frappe.whitelist(allow_guest=True)
def check_if_user_has_membership():
    form_data = frappe.local.form_dict
    phone = form_data.get('phone')
    if not phone:
        return 0
    if frappe.db.exists("Customer", {"phone": phone}):
        customer = frappe.db.get_value("Customer", {"phone":phone}, "name")
        if frappe.db.exists("Subscription", {"party": customer }):
            return 1
    return 0

@frappe.whitelist(allow_guest=True)
def get_membership_pricing():
    price = frappe.db.get_value("Item Price", {"item_code": "Dink Patron Membership", "price_list": "Standard Selling"}, "price_list_rate")
    return price

@frappe.whitelist()
def get_events():
    data = frappe.local.form_dict
    location = data.get('location')
    if not location:
        return {
            "success_key": 0,
            "message": "Please pass location"
        }
    if not frappe.db.exist("Dink Event", {"location": location}):
        return {
            "success_key": 0,
            "message": "Event Not Found"
        }
    doc = frappe.get_doc("Dink Event", {"location": location})

    event_facilities = []
    location_facilities = []
    things_to_know = []
    for facility in doc.event_facilities:
        event_facilities.append({
            "title": facility.title,
            "sub_title": facility.sub_title
        })
    for facility in doc.location_facilities:
        location_facilities.append(facility.facility_name)
    for things in doc.things_to_keep_in_mind:
        things_to_know.append({
            "title": things.title,
            "sub_title": things.sub_title
        })
    
    data =  {
      "event_id": doc.name,
      "event_name": doc.event_name,
      "price": doc.price,
      "date": doc.date,
      "time": f'{doc.from_time} - {doc.to_time}',
      "spots_available": doc.spots_available,
      "image": frappe.utils.get_url(doc.image) or "",
      "event_info": doc.event_info,
      "event_facilities": event_facilities,
      "location_facilities": location_facilities, 
      "things_to_keep_in_mind": things_to_know
    }
    return {
        "success_key": 1,
        "message": "Events fetched successfully",
        "data": data
    }
@frappe.whitelist()
def register_event():
    data = frappe.local.form_dict
    user_id = data.get("user_id")
    user = data.get("user")
    mobile = data.get("mobile")
    event_id = data.get("event_id")
    players = data.get("players")

    date = frappe.utils.today()
    if not frappe.db.exists("User", user_id):
        return {
            "success_key": 0,
            "message": "User not found"
        }
    booking = frappe.new_doc("Event Booking")
    booking.user = user_id
    booking.user = user
    booking.mobile = mobile
    booking.event = event_id
    booking.players = players
    booking.date = date
    booking.save(ignore_permissions=True)
    booking.submit()
    frappe.db.commit()
    event = frappe.get_doc("Dink Event", event_id)

    return {
        "success_key": 1,
        "message": "Successfully registered for the event",
        "data": {
            "user_id": user_id,
            "user_name": user,
            "event_booking_id": booking.name,
            "event_id": event_id,
            "event_name": event.event_name,
            "event_location": event.location,
            "price": event.price,
            "players":  players,
            "date": date,
            "start_time": event.from_time,
            "end_time": event.to_time
        }
        }

@frappe.whitelist()
def modify_booking():
#      "user_id": "12345",
#   "booking_id": "abc123",
#   "new_date": "2024-08-24",
#   "new_time": "6:00 AM - 7:00 AM"
    data = frappe.local.form_dict
    user_id = data.get("user_id")
    booking_id = data.get("booking_id")
    new_date = data.get("new_date")
    new_time = data.get("new_time")
    if frappe.db.exists("Booking", booking_id):
        doc = frappe.get_doc("Booking", booking_id)
        doc.date = new_date
        doc.from_time = new_time
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        frappe.local.response["message"] = {
            "success_key": 1,
            "message": "Booking updated successfully"
        }
    else:
        frappe.local.response["message"] = {
            "success_key": 0,
            "message": "Booking not found"
        }
        return
@frappe.whitelist()
def cancel_booking():
    data = frappe.local.form_dict
    user_id = data.get("user_id")
    booking_id = data.get("booking_id")

    try:
        if frappe.db.exists("Booking", bookiing_id):
            doc = frappe.get_doc("Booking", booking_id):
            doc.cancel()
            frappe.db.commit()
            frappe.local.response["message"] = 
                {    
                "success_key": 1,
                "message": "Booking canceled successfully",
                "refund": "A refund of 100% will be processed within 7 business days."
                }
        else:
            frappe.local.response["message"] = {
                   
                "success_key": 1,
                "message": "Booking canceled successfully",
                "refund": "A refund of 100% will be processed within 7 business days."
            }

    except Exception as e:
        frappe.local.response["message"] = {
            "success_key": 0,
            "message": "Booking not found"
        }
        return

@frappe.whitelist()
def get_locations():
    locations = frappe.get_all("Court", fields=["name", "location", "image"])
    data = []
    for location in locations:
        data.append({
            "name": location.name,
            "location": location.location,
            "image": location.image
        })
    return data

@frappe.whitelist()
def get_plan():
    try:
        plans = frappe.get_all("Subscription Plan")
        for plan in plans:
            plan_doc = frappe.get_doc("Subscription Plan", plan.name)
            benefits = []
            for benefit in plan_doc.plan_benefits:
                benefits.append(benefit.benefit)
            data.append({
                "plan_id": plan_doc.name,
                "plan_name": plan_doc.plan_name,
                "description": plan_doc.custom_description,
                "price": plan_doc.cost,
                "duration": plan_doc.billing_interval,
                "benefits": benefits
            })
        frappe.local.response["message"] = {
            "success_key": 1,
            "message": "Membership plans fetched successfully",
            "data": data
        }
    except Exception as e:
        frappe.local.response["message"] = {
            "success_key": 0,
            "message": "Error fetching membership plans"
        }
        return

@frappe.whitelist()
def get_prodcuts():
    form_data = frappe.local.form_dict
    category_id = form_data.get("category_id")
    if category_id:
        products = frappe.get_all("Item", {"item_group": category_id})
    else:
        products = frappe.get_all("Item")
    data = []
    if not products:
        frappe.local.response["message"] = {
            "success_key": 0,
            "message": "No products found"
        }
        return
    for product in products:
        doc = frappe.get_doc("Item", product.name)
        data.append({
            "product_id": doc.name,
            "product_name": doc.item_name,
            "product_thumbnail": frappe.utils.get_url(doc.image) or "",
            "product_price": doc.standard_selling_rate if doc.standard_selling_rate else frappe.db.get_value("Item Price", {"item_code": doc.item_code, "price_list": "Standard Selling"}, "price_list_rate") or 0,
            "category_id": doc.item
        })
    frappe.local.response["message"] = {
        "success_key": 1,
        "message": "Products fetched successfully",
        "data": data
    }
@frappe.whitelist()
def get_product_category():
    categories = frappe.get_all("Item Group")
    data = []
    for category in categories:
        doc = frappe.get_doc("Item Group", category.name)
        data.append({
            "category_id": doc.name,
            "category_name": doc.item_group_name,
            "category_thumbnail": frappe.utils.get_url(doc.image) or "",
            "total_products": len(frappe.get_all("Item", {"item_group": doc.name}))

        })
    frappe.local.response["message"] = {
        "success_key": 1,
        "message": "Product categories fetched successfully",
        "data": data
    }

