import frappe
from frappe.model.document import Document

class WhatsAppCarouselParameters(Document):
    """WhatsApp Carousel Parameters doctype controller."""
    
    def validate(self):
        """Validate carousel parameter data."""
        self.validate_parameter_type()
        self.validate_variable_name()
        self.validate_card_index()
    
    def validate_parameter_type(self):
        """Validate parameter type."""
        valid_types = ["body_variable", "card_header", "card_body"]
        if self.parameter_type not in valid_types:
            frappe.throw(f"Invalid parameter type. Must be one of: {', '.join(valid_types)}")
    
    def validate_variable_name(self):
        """Validate variable name format."""
        if not self.variable_name:
            frappe.throw("Variable name is required")
        
        # Check if variable name follows {{number}} format
        import re
        if not re.match(r'^\{\{\d+\}\}$', self.variable_name):
            frappe.throw("Variable name must be in format {{number}} (e.g., {{1}}, {{2}})")
    
    def validate_card_index(self):
        """Validate card index for card-specific parameters."""
        if self.parameter_type in ["card_header", "card_body"]:
            if not self.card_index:
                frappe.throw("Card index is required for card-specific parameters")
            if self.card_index < 0:
                frappe.throw("Card index must be 0 or greater")
    
    def get_parameter_value(self, doc):
        """Get the parameter value from the document."""
        if not self.field_name:
            return self.default_value
        
        # Get value from document field
        value = doc.get(self.field_name)
        
        # If value is empty, use default
        if not value and self.default_value:
            return self.default_value
        
        return value
    
    def get_parameter_payload(self, doc):
        """Get the parameter payload for WhatsApp API."""
        value = self.get_parameter_value(doc)
        
        if not value:
            return None
        
        return {
            "type": "text",
            "text": str(value)
        } 