# Copyright (c) 2025, Shridhar Patil and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document


class WhatsAppButtonParameters(Document):
    """WhatsApp Button Parameters."""
    
    def validate(self):
        """Validate button parameter configuration."""
        if self.button_type == "QUICK_REPLY" and not self.payload:
            frappe.throw("Payload is required for Quick Reply buttons")
        
        if self.button_type == "URL" and not self.url:
            frappe.throw("URL is required for URL buttons")
            
        if self.button_type == "PHONE_NUMBER" and not self.phone_number:
            frappe.throw("Phone number is required for Phone Number buttons")
            
        if self.button_type == "FLOW" and not self.flow_token:
            frappe.throw("Flow Token is required for Flow buttons")
            
        if self.button_type == "COPY_CODE" and not self.copy_code_example:
            frappe.throw("Copy code example is required for Copy Code buttons") 