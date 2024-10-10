# Copyright (c) 2024, Erpera and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Booking(Document):
	def on_submit(self):
		for slot in self.slots:
			schedule = frappe.new_doc("Court Schedules")
			schedule.court = frappe.db.get_value("Location Courts", self.court, "court")
			schedule.date = self.date
			schedule.time = slot.time
			schedule.court_number = self.court
			schedule.save()
			frappe.db.commit()
			# schedule.court_number = 
			
			
	def create_invoice(self):
		pass