# Copyright (c) 2025, Frappe Whatsapp and Contributors
# See license.txt

import frappe

def execute():
    """Add FLOW button support to existing installations."""
    
    # Update WhatsApp Button Parameters doctype
    if frappe.db.exists("DocType", "WhatsApp Button Parameters"):
        doc = frappe.get_doc("DocType", "WhatsApp Button Parameters")
        
        # Add FLOW to button type options
        for field in doc.fields:
            if field.fieldname == "button_type":
                if "FLOW" not in field.options:
                    field.options += "\nFLOW"
                break
        
        # Add flow_token field if it doesn't exist
        existing_fields = [f.fieldname for f in doc.fields]
        
        if "flow_token" not in existing_fields:
            doc.append("fields", {
                "fieldname": "flow_token",
                "fieldtype": "Data",
                "label": "Flow Token",
                "description": "Dynamic Flow Token. Use {{field_name}} to reference document fields",
                "depends_on": "eval:doc.button_type == 'FLOW'"
            })
        
        doc.save()
    
    # Update WhatsApp Template Buttons doctype
    if frappe.db.exists("DocType", "WhatsApp Template Buttons"):
        doc = frappe.get_doc("DocType", "WhatsApp Template Buttons")
        
        # Add FLOW to button type options
        for field in doc.fields:
            if field.fieldname == "button_type":
                if "FLOW" not in field.options:
                    field.options += "\nFLOW"
                break
        
        # Add flow_id, flow_action, and navigate_screen fields if they don't exist
        existing_fields = [f.fieldname for f in doc.fields]
        
        if "flow_id" not in existing_fields:
            doc.append("fields", {
                "fieldname": "flow_id",
                "fieldtype": "Data",
                "label": "Flow ID",
                "description": "Flow ID from Meta template configuration",
                "depends_on": "eval:doc.button_type == 'FLOW'"
            })
        
        if "flow_action" not in existing_fields:
            doc.append("fields", {
                "fieldname": "flow_action",
                "fieldtype": "Data",
                "label": "Flow Action",
                "description": "Flow action from Meta template configuration",
                "depends_on": "eval:doc.button_type == 'FLOW'"
            })
        
        if "navigate_screen" not in existing_fields:
            doc.append("fields", {
                "fieldname": "navigate_screen",
                "fieldtype": "Data",
                "label": "Navigate Screen",
                "description": "Navigate screen from Meta template configuration",
                "depends_on": "eval:doc.button_type == 'FLOW'"
            })
        
        doc.save()
    
    frappe.db.commit() 