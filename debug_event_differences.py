#!/usr/bin/env python3
"""
Debug script to understand the difference between after_insert and after_save events
in WhatsApp notification processing.
"""

import frappe
import json

def debug_event_differences():
    """Debug the differences between after_insert and after_save events."""
    
    print("🔍 Debugging Event Differences")
    print("=" * 50)
    
    # Test with a sample document
    try:
        # Get a test document (you can change this to your specific doctype)
        test_doctype = "Lead"  # Change this to your doctype
        test_docname = "CRM-LEAD-2025-00073"  # Change this to your document name
        
        doc = frappe.get_doc(test_doctype, test_docname)
        doc_data = doc.as_dict()
        
        print(f"📄 Testing with {test_doctype}: {test_docname}")
        print(f"Document state: {doc.docstatus}")
        print(f"Document modified: {doc.modified}")
        print(f"Document creation: {doc.creation}")
        
        # Test the button processing
        from frappe_whatsapp.frappe_whatsapp.utils.button_utils import process_dynamic_payload
        
        # Test payload processing
        test_payload = "{{name}}_test_payload"
        result = process_dynamic_payload(test_payload, doc, doc_data)
        
        print(f"\n🧪 Payload Processing Test:")
        print(f"Template: '{test_payload}'")
        print(f"Result: '{result}'")
        print(f"Doc data keys: {list(doc_data.keys())[:10]}...")  # Show first 10 keys
        
        # Check if the document has the expected field
        if hasattr(doc, 'name'):
            print(f"Document name field: {doc.name}")
            print(f"Doc_data name field: {doc_data.get('name', 'NOT_FOUND')}")
        
        # Test with different field types
        print(f"\n🔧 Field Value Tests:")
        for field in ['name', 'lead_name', 'email_id', 'mobile_no']:
            if hasattr(doc, field):
                doc_value = getattr(doc, field)
                data_value = doc_data.get(field, 'NOT_FOUND')
                print(f"  {field}: doc={doc_value}, data={data_value}")
        
        # Test the notification mapping
        print(f"\n📋 Notification Mapping Test:")
        from frappe_whatsapp.frappe_whatsapp.utils import get_notifications_map
        notification_map = get_notifications_map()
        
        if test_doctype in notification_map:
            print(f"Notifications for {test_doctype}:")
            for event, notifications in notification_map[test_doctype].items():
                print(f"  {event}: {notifications}")
        else:
            print(f"No notifications configured for {test_doctype}")
            
    except Exception as e:
        print(f"❌ Error during debugging: {str(e)}")
        import traceback
        traceback.print_exc()

def test_specific_notification(notification_name):
    """Test a specific WhatsApp notification."""
    
    print(f"\n🎯 Testing Specific Notification: {notification_name}")
    print("-" * 40)
    
    try:
        notification = frappe.get_doc("WhatsApp Notification", notification_name)
        
        print(f"Notification Type: {notification.notification_type}")
        print(f"Reference DocType: {notification.reference_doctype}")
        print(f"DocType Event: {notification.doctype_event}")
        print(f"Template: {notification.template}")
        print(f"Button Parameters Count: {len(notification.button_parameters) if notification.button_parameters else 0}")
        
        if notification.button_parameters:
            print(f"\nButton Parameters:")
            for i, param in enumerate(notification.button_parameters):
                print(f"  {i+1}. Type: {param.button_type}")
                print(f"     Payload: {param.payload}")
                print(f"     Button Index: {param.button_index}")
        
        # Test with a sample document
        if notification.reference_doctype:
            test_docs = frappe.get_all(notification.reference_doctype, limit=1)
            if test_docs:
                test_doc = frappe.get_doc(notification.reference_doctype, test_docs[0].name)
                print(f"\nTesting with document: {test_doc.name}")
                
                # Test button processing
                if notification.button_parameters:
                    from frappe_whatsapp.frappe_whatsapp.utils.button_utils import get_template_buttons_with_dynamic_values
                    
                    template = frappe.get_doc("WhatsApp Templates", notification.template)
                    buttons = get_template_buttons_with_dynamic_values(
                        template, 
                        notification.button_parameters, 
                        test_doc, 
                        test_doc.as_dict()
                    )
                    
                    print(f"Processed Buttons:")
                    for i, button in enumerate(buttons):
                        print(f"  {i+1}. {button}")
                        
    except Exception as e:
        print(f"❌ Error testing notification: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Initialize Frappe
    frappe.init(site='your-site-name')  # Change this to your site name
    frappe.connect()
    
    # Run the debug
    debug_event_differences()
    
    # Test specific notification if provided
    # test_specific_notification("Your-Notification-Name")
