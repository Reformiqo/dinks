import frappe
from datetime import datetime, timedelta
from frappe.utils import getdate, cint, today
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
        "evening": evening_slots
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
    # return form_data
    
    if frappe.db.exists("Customer", {"email": email, "phone": phone}):
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
    

    for time in time_schedules:
        booking.append("slots", {
            "time": time
        })
    
    booking.save(ignore_permissions=True)
    booking.submit()


    invoice = frappe.new_doc("Sales Invoice")
    invoice.customer = customer.name
    invoice.append("items", {
        "item_code": "Court Booking",
        "qty": 1,
        "rate": amount
    })
    if pay_at_court and pay_at_court == 1:
        frappe.db.set_value("Booking", booking.name, "pay_at_court", 1)

    else:
        invoice.is_pos = 1
        invoice.append("payments", {
            "mode_of_payment": "Razorpay",
            "amount": amount
            })
        invoice.paid_amount = amount
    invoice.save(ignore_permissions=True)
    invoice.submit()
    frappe.db.commit()
    # razorpay_invoice = create_invoice(invoice)
    frappe.sendmail(
        recipients=email,
        subject="Court Booking Confirmation",
        message=f"Hello {first_name}, your court booking has been confirmed. and your booking id is {booking.name}"
    )
    return {'booking': booking.name}


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
        "callback_url": "https://dinkstest.erpera.io/buy/play-now/confirmation",
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
        "callback_url": "https://dinkstest.erpera.io/buy/become-a-member/confirmation",
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

    return customer
@frappe.whitelist(allow_guest=True)
def get_booking():
    form_data = frappe.local.form_dict
    name = form_data.get('name')
    booking = frappe.get_doc("Booking", {"name": name})

    return booking


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