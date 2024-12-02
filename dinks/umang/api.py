import frappe
from datetime import datetime, timedelta
from frappe.utils import getdate, cint, today, flt
import razorpay
import frappe
from datetime import datetime, timedelta
import json

@frappe.whitelist(allow_guest=True)
def test():
    return "test"