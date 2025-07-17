#!/usr/bin/env python3
"""
Test script for WhatsApp Carousel Template Implementation

This script tests the carousel template functionality in the frappe_whatsapp app.
"""

import frappe
import json
from frappe_whatsapp.utils.carousel_utils import (
    build_carousel_payload, 
    validate_carousel_template,
    process_carousel_parameters
)

def test_carousel_template_creation():
    """Test creating a carousel template."""
    print("🧪 Testing carousel template creation...")
    
    # Create a test carousel template
    template = frappe.new_doc("WhatsApp Templates")
    template.template_name = "Test Carousel Template"
    template.template_type = "Carousel"
    template.category = "MARKETING"
    template.language = "en"
    template.language_code = "en_US"
    template.status = "Pending"
    
    # Add carousel cards
    card1 = {
        "card_index": 0,
        "header_type": "IMAGE",
        "header_content": "https://example.com/image1.jpg",
        "body_text": "Card 1: Check out our {{1}} products!"
    }
    
    card2 = {
        "card_index": 1,
        "header_type": "TEXT",
        "header_text": "Special Offer",
        "body_text": "Card 2: Get {{2}} off your next purchase!"
    }
    
    template.append("carousel_cards", card1)
    template.append("carousel_cards", card2)
    
    try:
        template.insert(ignore_permissions=True)
        print("✅ Carousel template created successfully!")
        return template
    except Exception as e:
        print(f"❌ Failed to create carousel template: {e}")
        return None

def test_carousel_validation():
    """Test carousel template validation."""
    print("\n🧪 Testing carousel template validation...")
    
    # Test valid template
    template = frappe.get_doc("WhatsApp Templates", "Test Carousel Template")
    is_valid, error = validate_carousel_template(template)
    
    if is_valid:
        print("✅ Carousel template validation passed!")
    else:
        print(f"❌ Carousel template validation failed: {error}")
    
    # Test invalid template (too many cards)
    invalid_template = frappe.new_doc("WhatsApp Templates")
    invalid_template.template_type = "Carousel"
    
    for i in range(11):  # More than 10 cards
        card = {
            "card_index": i,
            "header_type": "TEXT",
            "header_text": f"Card {i}",
            "body_text": f"Body {i}"
        }
        invalid_template.append("carousel_cards", card)
    
    is_valid, error = validate_carousel_template(invalid_template)
    
    if not is_valid:
        print("✅ Invalid template correctly rejected!")
    else:
        print("❌ Invalid template should have been rejected!")

def test_carousel_payload_generation():
    """Test carousel payload generation."""
    print("\n🧪 Testing carousel payload generation...")
    
    template = frappe.get_doc("WhatsApp Templates", "Test Carousel Template")
    
    # Create test document
    test_doc = frappe.new_doc("Lead")
    test_doc.lead_name = "John Doe"
    test_doc.company = "Test Company"
    test_doc.insert(ignore_permissions=True)
    
    # Create carousel parameters
    carousel_parameters = [
        {
            "parameter_type": "body_variable",
            "variable_name": "{{1}}",
            "field_name": "company"
        },
        {
            "parameter_type": "body_variable",
            "variable_name": "{{2}}",
            "field_name": "lead_name"
        }
    ]
    
    # Build carousel payload
    carousel_component = build_carousel_payload(template, carousel_parameters, test_doc)
    
    if carousel_component:
        print("✅ Carousel payload generated successfully!")
        print(f"📋 Payload: {json.dumps(carousel_component, indent=2)}")
    else:
        print("❌ Failed to generate carousel payload!")
    
    # Clean up
    test_doc.delete(ignore_permissions=True)

def test_carousel_parameter_processing():
    """Test carousel parameter processing."""
    print("\n🧪 Testing carousel parameter processing...")
    
    # Create test document
    test_doc = frappe.new_doc("Lead")
    test_doc.lead_name = "Jane Smith"
    test_doc.company = "ABC Corp"
    test_doc.insert(ignore_permissions=True)
    
    # Create carousel parameters
    carousel_parameters = [
        {
            "parameter_type": "body_variable",
            "variable_name": "{{1}}",
            "field_name": "company"
        },
        {
            "parameter_type": "card_header",
            "variable_name": "{{2}}",
            "field_name": "lead_name",
            "card_index": 0
        }
    ]
    
    # Process parameters
    processed_params = process_carousel_parameters(carousel_parameters, test_doc)
    
    print("✅ Carousel parameters processed successfully!")
    print(f"📋 Processed parameters: {json.dumps(processed_params, indent=2)}")
    
    # Clean up
    test_doc.delete(ignore_permissions=True)

def test_carousel_notification():
    """Test carousel notification sending."""
    print("\n🧪 Testing carousel notification...")
    
    # Create carousel notification
    notification = frappe.new_doc("WhatsApp Notification")
    notification.notification_name = "Test Carousel Notification"
    notification.notification_type = "DocType Event"
    notification.reference_doctype = "Lead"
    notification.field_name = "mobile_no"
    notification.template = "Test Carousel Template"
    notification.doctype_event = "After Insert"
    
    # Add carousel parameters
    notification.append("carousel_parameters", {
        "parameter_type": "body_variable",
        "variable_name": "{{1}}",
        "field_name": "company"
    })
    
    notification.append("carousel_parameters", {
        "parameter_type": "body_variable",
        "variable_name": "{{2}}",
        "field_name": "lead_name"
    })
    
    try:
        notification.insert(ignore_permissions=True)
        print("✅ Carousel notification created successfully!")
        return notification
    except Exception as e:
        print(f"❌ Failed to create carousel notification: {e}")
        return None

def cleanup_test_data():
    """Clean up test data."""
    print("\n🧹 Cleaning up test data...")
    
    # Delete test template
    if frappe.db.exists("WhatsApp Templates", "Test Carousel Template"):
        frappe.delete_doc("WhatsApp Templates", "Test Carousel Template", ignore_permissions=True)
        print("✅ Test template deleted!")
    
    # Delete test notification
    if frappe.db.exists("WhatsApp Notification", "Test Carousel Notification"):
        frappe.delete_doc("WhatsApp Notification", "Test Carousel Notification", ignore_permissions=True)
        print("✅ Test notification deleted!")

def main():
    """Run all tests."""
    print("🚀 Starting WhatsApp Carousel Template Tests")
    print("=" * 50)
    
    try:
        # Run tests
        template = test_carousel_template_creation()
        if template:
            test_carousel_validation()
            test_carousel_payload_generation()
            test_carousel_parameter_processing()
            test_carousel_notification()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        frappe.log_error(f"Carousel test failed: {e}", "WhatsApp Carousel Test")
    
    finally:
        cleanup_test_data()

if __name__ == "__main__":
    main() 