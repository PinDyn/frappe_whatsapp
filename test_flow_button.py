#!/usr/bin/env python3
"""
Test script for FLOW button functionality in frappe_whatsapp app.
This script demonstrates how to create and send a template with FLOW buttons.
"""

import frappe
import json

def test_flow_button_creation():
    """Test creating a template with FLOW buttons."""
    
    # Create a test template with FLOW button
    template = frappe.new_doc("WhatsApp Templates")
    template.template_name = "Test Flow Template"
    template.actual_name = "test_flow_template"
    template.template = "Hello! Would you like to start our interactive flow?"
    template.language_code = "en"
    template.category = "UTILITY"
    
    # Add FLOW button
    template.append("buttons", {
        "button_text": "Start Flow",
        "button_type": "FLOW",
        "flow_id": "1081813126775012",
        "flow_token": "test123"
    })
    
    try:
        template.insert()
        print(f"✅ Template created successfully: {template.name}")
        return template.name
    except Exception as e:
        print(f"❌ Failed to create template: {e}")
        return None

def test_flow_button_notification():
    """Test creating a notification with FLOW button parameters."""
    
    template_name = test_flow_button_creation()
    if not template_name:
        return
    
    # Create a test notification
    notification = frappe.new_doc("WhatsApp Notification")
    notification.notification_name = "Test Flow Notification"
    notification.reference_doctype = "Customer"
    notification.doctype_event = "After Insert"
    notification.template = template_name
    notification.notification_type = "DocType Event"
    
    # Add FLOW button parameters
    notification.append("button_parameters", {
        "button_index": 0,
        "button_type": "FLOW",
        "flow_id": "1081813126775012",
        "flow_token": "{{name}}"  # Dynamic flow token from document
    })
    
    try:
        notification.insert()
        print(f"✅ Notification created successfully: {notification.name}")
        return notification.name
    except Exception as e:
        print(f"❌ Failed to create notification: {e}")
        return None

def test_flow_button_sending():
    """Test sending a message with FLOW button."""
    
    # Create a test customer
    customer = frappe.new_doc("Customer")
    customer.customer_name = "Test Customer"
    customer.customer_type = "Company"
    
    try:
        customer.insert()
        print(f"✅ Customer created: {customer.name}")
        
        # Create a test WhatsApp message
        message = frappe.new_doc("WhatsApp Message")
        message.type = "Outgoing"
        message.message_type = "Template"
        message.template = "test_flow_template"
        message.to = "27726017261"
        message.reference_doctype = "Customer"
        message.reference_name = customer.name
        
        # Set custom data for dynamic flow token
        message.flags.custom_ref_doc = {"name": "dynamic_flow_token_123"}
        
        message.insert()
        print(f"✅ Message created: {message.name}")
        
        return message.name
        
    except Exception as e:
        print(f"❌ Failed to test flow button sending: {e}")
        return None

def cleanup_test_data():
    """Clean up test data."""
    try:
        # Delete test templates
        frappe.db.sql("DELETE FROM `tabWhatsApp Templates` WHERE template_name LIKE 'Test%'")
        
        # Delete test notifications
        frappe.db.sql("DELETE FROM `tabWhatsApp Notification` WHERE notification_name LIKE 'Test%'")
        
        # Delete test messages
        frappe.db.sql("DELETE FROM `tabWhatsApp Message` WHERE template = 'test_flow_template'")
        
        # Delete test customers
        frappe.db.sql("DELETE FROM `tabCustomer` WHERE customer_name = 'Test Customer'")
        
        frappe.db.commit()
        print("✅ Test data cleaned up")
        
    except Exception as e:
        print(f"❌ Failed to cleanup: {e}")

if __name__ == "__main__":
    print("🧪 Testing FLOW Button Functionality")
    print("=" * 50)
    
    # Run tests
    test_flow_button_creation()
    test_flow_button_notification()
    test_flow_button_sending()
    
    # Cleanup
    print("\n🧹 Cleaning up test data...")
    cleanup_test_data()
    
    print("\n✅ FLOW button tests completed!") 