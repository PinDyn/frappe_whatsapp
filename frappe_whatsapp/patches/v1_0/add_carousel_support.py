# Copyright (c) 2025, Frappe Whatsapp and Contributors
# See license.txt

import frappe

def execute():
    """Add carousel template support to WhatsApp Templates."""
    
    # Add template_type field to existing templates
    if not frappe.db.exists("Custom Field", {"dt": "WhatsApp Templates", "fieldname": "template_type"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "WhatsApp Templates",
            "fieldname": "template_type",
            "fieldtype": "Select",
            "label": "Template Type",
            "options": "Template\nCarousel",
            "default": "Template",
            "insert_after": "template_name"
        }).insert(ignore_permissions=True)
    
    # Add carousel_cards field to existing templates
    if not frappe.db.exists("Custom Field", {"dt": "WhatsApp Templates", "fieldname": "carousel_cards"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "WhatsApp Templates",
            "fieldname": "carousel_cards",
            "fieldtype": "Table",
            "label": "Carousel Cards",
            "options": "WhatsApp Carousel Cards",
            "depends_on": "eval:doc.template_type == 'Carousel'",
            "insert_after": "buttons"
        }).insert(ignore_permissions=True)
    
    # Add carousel_parameters field to existing notifications
    if not frappe.db.exists("Custom Field", {"dt": "WhatsApp Notification", "fieldname": "carousel_parameters"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "WhatsApp Notification",
            "fieldname": "carousel_parameters",
            "fieldtype": "Table",
            "label": "Carousel Parameters",
            "options": "WhatsApp Carousel Parameters",
            "depends_on": "eval:doc.template && frappe.db.get_value('WhatsApp Templates', doc.template, 'template_type') == 'Carousel'",
            "insert_after": "button_parameters"
        }).insert(ignore_permissions=True)
    
    # Create WhatsApp Carousel Cards doctype if it doesn't exist
    if not frappe.db.exists("DocType", "WhatsApp Carousel Cards"):
        frappe.get_doc({
            "doctype": "DocType",
            "name": "WhatsApp Carousel Cards",
            "istable": 1,
            "module": "Frappe Whatsapp",
            "fields": [
                {
                    "fieldname": "card_index",
                    "fieldtype": "Int",
                    "label": "Card Index",
                    "reqd": 1,
                    "unique": 1
                },
                {
                    "fieldname": "header_type",
                    "fieldtype": "Select",
                    "label": "Header Type",
                    "options": "IMAGE\nVIDEO\nTEXT",
                    "reqd": 1
                },
                {
                    "depends_on": "eval:doc.header_type == 'IMAGE' || doc.header_type == 'VIDEO'",
                    "fieldname": "header_content",
                    "fieldtype": "Data",
                    "label": "Header Content",
                    "description": "URL for media or asset handle"
                },
                {
                    "depends_on": "eval:doc.header_type == 'TEXT'",
                    "fieldname": "header_text",
                    "fieldtype": "Data",
                    "label": "Header Text",
                    "description": "Text header (max 60 characters)"
                },
                {
                    "fieldname": "body_text",
                    "fieldtype": "Text",
                    "label": "Body Text",
                    "description": "Card body text with variables like {{1}}, {{2}} (max 160 characters)"
                },
                {
                    "description": "Add buttons to this card (max 2 buttons per card)",
                    "fieldname": "buttons",
                    "fieldtype": "Table",
                    "label": "Buttons",
                    "options": "WhatsApp Template Buttons"
                }
            ]
        }).insert(ignore_permissions=True)
    
    # Create WhatsApp Carousel Parameters doctype if it doesn't exist
    if not frappe.db.exists("DocType", "WhatsApp Carousel Parameters"):
        frappe.get_doc({
            "doctype": "DocType",
            "name": "WhatsApp Carousel Parameters",
            "istable": 1,
            "module": "Frappe Whatsapp",
            "fields": [
                {
                    "fieldname": "parameter_type",
                    "fieldtype": "Select",
                    "label": "Parameter Type",
                    "options": "body_variable\ncard_header\ncard_body",
                    "reqd": 1
                },
                {
                    "fieldname": "variable_name",
                    "fieldtype": "Data",
                    "label": "Variable Name",
                    "description": "e.g., {{1}}, {{2}} for body or card-specific variables",
                    "reqd": 1
                },
                {
                    "fieldname": "field_name",
                    "fieldtype": "Data",
                    "label": "Field Name",
                    "description": "Document field to use for replacement"
                },
                {
                    "depends_on": "eval:doc.parameter_type == 'card_header' || doc.parameter_type == 'card_body'",
                    "fieldname": "card_index",
                    "fieldtype": "Int",
                    "label": "Card Index",
                    "description": "For card-specific parameters"
                },
                {
                    "fieldname": "default_value",
                    "fieldtype": "Data",
                    "label": "Default Value",
                    "description": "Default value if field is empty"
                }
            ]
        }).insert(ignore_permissions=True)
    
    frappe.db.commit()
    print("✅ Carousel template support added successfully!") 