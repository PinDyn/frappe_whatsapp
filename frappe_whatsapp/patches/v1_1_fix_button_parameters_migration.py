# Copyright (c) 2025, Frappe Whatsapp and Contributors
# See license.txt

import frappe

def execute():
    """Fix migration issue with WhatsApp Button Parameters table"""
    
    # Check if the table exists
    if not frappe.db.table_exists("tabWhatsApp Button Parameters"):
        frappe.log_error("WhatsApp Button Parameters table does not exist", "Migration Error")
        return
    
    # Check if there are any existing WhatsApp Notification records with button_parameters
    # that might be causing the parent column error
    try:
        # Get all WhatsApp Notification records
        notifications = frappe.get_all("WhatsApp Notification", fields=["name"])
        
        for notification in notifications:
            try:
                # Try to load each notification to see if it causes the parent column error
                doc = frappe.get_doc("WhatsApp Notification", notification.name)
                # If successful, continue
            except Exception as e:
                if "Unknown column 'parent' in 'WHERE'" in str(e):
                    # This notification has button_parameters data that's causing issues
                    # Clear the button_parameters data
                    frappe.db.sql("""
                        DELETE FROM `tabWhatsApp Button Parameters` 
                        WHERE parent = %s
                    """, notification.name)
                    frappe.db.commit()
                    frappe.log_error(f"Cleared button_parameters for notification {notification.name}", "Migration Fix")
                else:
                    # Re-raise other errors
                    raise e
                    
    except Exception as e:
        frappe.log_error(f"Error during button parameters migration fix: {str(e)}", "Migration Error") 