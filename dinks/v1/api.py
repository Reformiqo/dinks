import frappe
from datetime import datetime, timedelta
from frappe.utils import getdate, cint, today, flt
import razorpay
import frappe
from datetime import datetime, timedelta
import json

@frappe.whitelist(allow_guest=True)
def get_days(location):
    today = datetime.today()
    data = []
    for i in range(30):
        next_date = today + timedelta(days=i)
        day_name = next_date.strftime('%A')  
        date_str = next_date.strftime('%Y-%m-%d') 
        
        data.append({
            "day_name": day_name,
            "date": date_str,
        })
    return data
@frappe.whitelist(allow_guest=True)
def get_next_30_days(location):
    today = datetime.today()
    data = []
    for i in range(30):
        next_date = today + timedelta(days=i)
        schedules = frappe.get_all("Court Schedules",{"court": location, "date": getdate(next_date)}, ["time", ])
        courts = frappe.get_all("Location Courts", {"court": location}, ["court_number", "status"])
        day_name = next_date.strftime('%A')  
        date_str = next_date.strftime('%Y-%m-%d') 
        schedule_data = []
        for schedule in schedules:
            
            schedule_data.append({
                "time": schedule.time,
                "courts": courts
            })
    
        data.append({
            "weekday": day_name[:3],
            "day": date_str.split("-")[-1],
            "date": date_str,
            "schedules": schedule_data,

        })
    
    return data
@frappe.whitelist(allow_guest=True)
def get_rates():
    rates = frappe.get_all("Booking Price")
    data = []
    for rate in rates:
        doc = frappe.get_doc("Booking Price", rate.name)
        categories = dict()
        for c in doc.categories:
            # categories.append(
            #     {
            #     c.slot_category:c.rate
            #     })
            categories[c.slot_category] = c.rate
    
        data.append({
            "day": doc.day,
            "categories": categories
        })
    return data


@frappe.whitelist(allow_guest=True)
def get_available_courts():
    form_data = frappe.local.form_dict
    location = form_data.get("location")
    date = form_data.get("date")
    time_schedules = form_data.get("time_schedules")
    court_data = []
    booked_courts = []
    for time in time_schedules:
        schedules = frappe.get_all("Court Schedules", {"court": location, "date": getdate(date), "time": time}, ["court_number"])
        for s in schedules:
            if s.get("court_number") not in booked_courts:
                booked_courts.append(
                    s.get("court_number"))
    courts = frappe.get_all("Location Courts", {"court": location}, ["court_number", "name"], order_by="court_number")
    for court in courts:
        if court.get("name") not in booked_courts:
            court_data.append({
                "court_number": court.get("court_number"),
                "status": "Available"
            })
            # add the status of the court
        else:
            court_data.append({
                "court_number": court.get("court_number"),
                "status": "Booked"
            })
    return court_data

@frappe.whitelist(allow_guest=True)
def get_time_slots():
    slots = frappe.get_all("Time Slots", fields=["name", "slot_category"])
    moring_slots = []
    afternoon_slots = []
    evening_slots = []
    for slot in slots:
        category = slot.get("slot_category")
        if category == "Morning":
            moring_slots.append(slot.get("name"))
        elif category == "Afternoon":
            afternoon_slots.append(slot.get("name"))
        else:
            evening_slots.append(slot.get("name"))
    
    return {
        "morning": moring_slots,
        "afternoon": afternoon_slots,
        "evening": evening_slots,
    }   
@frappe.whitelist(allow_guest=True)
def get_everything(location, ):
    dates = get_days(location)  # Fetch next 30 days
    schedule_data = []

    # Fetch all courts for the location at once
    courts = frappe.get_all("Location Courts", filters={"court": location}, fields=["name", "court_number", "status"], order_by="court_number")

    # Loop through dates and check court schedules
    for date in dates:
        date_str = date.get("date")
        court_data = []
        for court in courts:
            schedules = frappe.get_all("Court Schedules", filters={"court": location, "date": date_str, "court_number": court.name}, fields=["court_number", "time"])
            # Find if the court has a schedule for the current date
            # scheduled_court = next((s for s in schedules if s.get("court_number") == court.get("name")), None)
            s_data = []
            for s in schedules:
                if s.get("court_number") == court.get("name"):
                    s_data.append({
                        "time": s.get("time")
                    })
            court_data.append({
                "court_number": court.get("court_number"),
                "schedules": s_data
            })
        
        
        schedule_data.append({
            "date": date_str,
            "court_data": court_data
        })

    return schedule_data

@frappe.whitelist(allow_guest=True)
def get_courts():
    courts = frappe.get_all("Court", fields=["name", "location", "image"])
    data = []
    for court in courts:
        data.append({
            "name": court.name,
            "location": court.location,
            "image": court.image
        })
    return data

@frappe.whitelist(allow_guest=True)
def get_court_schedules(location):
    schedules = frappe.get_all("Court Schedules", {"court": location}, ["court", "date", "time"])
    data = []
    for schedule in schedules:
        data.append({
            "court": schedule.court,
            "date": schedule.date,
            "time": schedule.time
        })
    return data

@frappe.whitelist(allow_guest=True)
def get_location_courts(court_name):
    courts = frappe.get_all("Location Courts", {"court": court_name}, ["name", "court_number", "court"])
    return courts


@frappe.whitelist(allow_guest=True)
def get_session():
    session = frappe.local.session
    return session.get("data")

@frappe.whitelist(allow_guest=True)
def create_booking():
    if frappe.local.form_dict.data is None:
          data = json.loads(frappe.local.request.get_data())
    else:
          data = json.loads(frappe.local.form_dict.data)
    
    form_data = data
    location = form_data.get("location")
    date = form_data.get("date")
    time_schedules = form_data.get("timeSchedules")
    email = form_data.get("email")
    first_name = form_data.get("first_name")
    last_name = form_data.get("last_name")
    phone = form_data.get("phone")
    court_number = form_data.get("court_number")
    weekday = form_data.get("weekday")
    amount = form_data.get("amount")
    pay_at_court = form_data.get("pay_at_court")
    players = form_data.get("player")
    time_period = form_data.get("time_period")
    # return form_data
    
    if frappe.db.exists("Customer", {"phone": phone}):
        customer = frappe.get_doc("Customer", {"email": email, "phone": phone})
    else:
        customer = frappe.get_doc({
            "doctype": "Customer",
            "email": email,
            "customer_name": f"{first_name} {last_name}",
            "phone": phone
        })
        customer.save(ignore_permissions=True)
        frappe.db.commit()
    
    court  = frappe.get_doc("Location Courts", {"court_number": court_number, "court": location})
    booking = frappe.new_doc("Booking")
    booking.customer = customer.name
    booking.court = court.name
    booking.date = date
    booking.players = players
    booking.pay_at_court = pay_at_court
    booking.time_period = time_period
    booking.pay_at_court
    
    
    for time in time_schedules:
        booking.append("slots", {
            "time": time
        })
    
    booking.save(ignore_permissions=True)

    booking.submit()

    location = frappe.get_doc("Location Courts", court.name)


    invoice = frappe.new_doc("Sales Invoice")
    invoice.customer = customer.name
    invoice.custom_booking_id = booking.name
    invoice.custom_court = booking.court
    invoice.custom_players = booking.players
    invoice.custom_time_period = booking.time_period
    invoice.custom_location = frappe.db.get_value("Court", location.court, "location")
   

    invoice.append("items", {
        "item_code": "Court Booking",
        "qty": 1,
        "rate": get_booking_price(booking.name)
    })
    

    paid  = frappe.db.get_value("Booking", booking.name, "pay_at_court")
    if paid == 0:
        invoice.is_pos = 1
        invoice.pos_profile = "Razorpay"

    invoice.save(ignore_permissions=True)
    invoice.submit()
    frappe.db.commit()
        
        
    # razorpay_invoice = create_invoice(invoice)
    frappe.sendmail(
        recipients=email,
        subject="Court Booking Confirmation",
        message=f"""Hello {first_name}, your court booking has been confirmed. and your booking id is {booking.name}
                    Below is the link to your booking
                    https://dinksports.erpera.io/buy/play-now/your-booking?booking={booking.name}
        """
    )
    return {'booking': booking.name}

@frappe.whitelist(allow_guest=True)
def get_booking_price(booking_id):
    booking = frappe.get_doc("Booking", booking_id)
    weekday = booking.date.strftime('%A')
    amount = 0
    for slot in booking.slots:
        amount += flt(frappe.db.get_value("Booking Price Details", {"parent": weekday, "slot_category": slot.category}, "rate"))

    return amount

@frappe.whitelist()
def create_invoice(doc, method=None):
    settings = frappe.get_doc("Razorpay Settings")
    id = settings.api_key
    secret = settings.get_password("api_secret")
    client = razorpay.Client(auth=(id, secret))

    items = []
    for item in doc.items:
        items.append({
            "name": item.item_code,
            "quantity": item.qty,
            "amount": cint(item.rate) * (100)
        })
    customer = {
        "name": doc.customer
    }
    data = {
        "type": "invoice",
        "description": "Invoice for the month of January 2020",
        "customer": customer,
        "line_items": items,
    }
    response = client.invoice.create(data)
    return response.get('short_url')

@frappe.whitelist(allow_guest=True)
def get_payment_link():
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
        "amount": cint(amount) * 100,
        "currency": "INR",
        "description": full_name,
        "callback_url": "https://dinksports.erpera.io/buy/play-now/confirmation",
        "callback_method": "get"
    }
    response = client.invoice.create(data)
    return response.get('short_url')

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

