#!/usr/bin/env python3
"""
Example: Proper Integration with Existing Frappe WhatsApp Architecture

This script demonstrates how to use carousel functionality with the existing system:
1. WhatsApp Templates doctype for template creation
2. WhatsApp Message doctype for sending
3. WhatsApp Notification doctype for automated notifications

Usage:
    python example_proper_integration.py
"""

import frappe
import json
from frappe_whatsapp.frappe_whatsapp.utils.carousel_utils import upload_attach_to_whatsapp

def create_carousel_template_example():
    """Example: Create a carousel template using the WhatsApp Templates doctype."""
    print("📝 Creating Carousel Template Example")
    print("=" * 50)
    
    try:
        # Create a new WhatsApp Template
        template = frappe.new_doc("WhatsApp Templates")
        template.template_name = "Sample Carousel Template"
        template.template_type = "Carousel"
        template.category = "MARKETING"
        template.language = "English"
        template.template = "Welcome to our amazing product! 🚀"  # Main body text
        
        # Add carousel cards
        for i in range(3):
            card = template.append("carousel_cards", {})
            card.card_index = i + 1
            
            # Set header (image)
            card.header_type = "IMAGE"
            # Note: In real usage, you would upload an image first and get the file URL
            # For this example, we'll use a placeholder
            card.header_content = "/files/sample_image.jpg"  # Replace with actual uploaded file URL
            
            # Set body text
            if i == 0:
                card.body_text = "Discover our amazing features! ✨"
            elif i == 1:
                card.body_text = "Get started with our platform today! 🎯"
            else:
                card.body_text = "Join thousands of satisfied customers! 🎉"
            
            # Add buttons
            button1 = card.append("buttons", {})
            button1.button_type = "QUICK_REPLY"
            button1.button_text = "Learn More"
            button1.payload = f"learn_more_{i+1}"
            
            if i == 0:  # Add second button only to first card
                button2 = card.append("buttons", {})
                button2.button_type = "URL"
                button2.button_text = "Visit Website"
                button2.url = "https://example.com"
        
        # Save the template
        template.insert()
        print(f"✅ Template created: {template.name}")
        
        # Create template in Meta (this will upload images and create the template)
        print("🔄 Creating template in Meta...")
        template.create_template_in_meta()
        print(f"✅ Template created in Meta with ID: {template.id}")
        print(f"📊 Status: {template.status}")
        
        return template
        
    except Exception as e:
        print(f"❌ Error creating template: {e}")
        return None

def send_carousel_message_example(template_name, phone_number):
    """Example: Send a carousel message using the WhatsApp Message doctype."""
    print(f"\n📱 Sending Carousel Message Example")
    print("=" * 50)
    
    try:
        # Create a new WhatsApp Message
        message = frappe.new_doc("WhatsApp Message")
        message.type = "Outgoing"
        message.message_type = "Template"
        message.template = template_name
        message.to = phone_number
        message.content_type = "text"
        
        # Add custom reference data if needed
        message.flags.custom_ref_doc = {
            "customer_name": "John Doe",
            "product_name": "Premium Plan",
            "discount": "50% off"
        }
        
        # Save and send the message
        message.insert()
        print(f"✅ Message sent: {message.name}")
        print(f"📊 Status: {message.status}")
        
        return message
        
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return None

def create_whatsapp_notification_example(template_name):
    """Example: Create a WhatsApp Notification for automated carousel messages."""
    print(f"\n🔔 Creating WhatsApp Notification Example")
    print("=" * 50)
    
    try:
        # Create a new WhatsApp Notification
        notification = frappe.new_doc("WhatsApp Notification")
        notification.template = template_name
        notification.enabled = 1
        notification.notification_type = "WhatsApp"
        notification.document_type = "Customer"  # Example doctype
        notification.field_name = "mobile_no"  # Field containing phone number
        
        # Set conditions (optional)
        notification.condition = "doc.customer_type == 'Premium'"
        
        # Add fields for template parameters
        field1 = notification.append("fields", {})
        field1.field_name = "customer_name"
        
        field2 = notification.append("fields", {})
        field2.field_name = "customer_type"
        
        # Save the notification
        notification.insert()
        print(f"✅ Notification created: {notification.name}")
        
        return notification
        
    except Exception as e:
        print(f"❌ Error creating notification: {e}")
        return None

def upload_image_example(image_path):
    """Example: Upload an image to WhatsApp and get the handle."""
    print(f"\n📤 Uploading Image Example")
    print("=" * 50)
    
    try:
        # First, create a File document in Frappe
        file_doc = frappe.new_doc("File")
        file_doc.file_name = "sample_image.jpg"
        file_doc.file_url = image_path
        file_doc.folder = "Home/Attachments/WhatsApp"
        file_doc.is_private = 0
        file_doc.insert()
        
        print(f"✅ File created: {file_doc.name}")
        print(f"📁 File URL: {file_doc.file_url}")
        
        # Upload to WhatsApp
        handle = upload_attach_to_whatsapp(file_doc.file_url)
        print(f"✅ Image uploaded to WhatsApp")
        print(f"🆔 Handle: {handle}")
        
        return handle, file_doc.file_url
        
    except Exception as e:
        print(f"❌ Error uploading image: {e}")
        return None, None

def main():
    """Main example function."""
    print("🚀 Frappe WhatsApp Carousel Integration Example")
    print("=" * 60)
    print("This example shows how to use carousel functionality with the existing system.")
    print()
    
    try:
        # Step 1: Upload an image (if you have one)
        print("Step 1: Image Upload")
        print("-" * 30)
        image_path = "/path/to/your/image.jpg"  # Replace with actual image path
        handle, file_url = upload_image_example(image_path)
        
        if not handle:
            print("⚠️  Skipping image upload for this example")
            file_url = "/files/sample_image.jpg"  # Placeholder
        
        # Step 2: Create carousel template
        print("\nStep 2: Template Creation")
        print("-" * 30)
        template = create_carousel_template_example()
        
        if not template:
            print("❌ Template creation failed. Exiting.")
            return
        
        # Step 3: Send carousel message
        print("\nStep 3: Message Sending")
        print("-" * 30)
        phone_number = "1234567890"  # Replace with actual phone number
        message = send_carousel_message_example(template.name, phone_number)
        
        # Step 4: Create notification
        print("\nStep 4: Notification Setup")
        print("-" * 30)
        notification = create_whatsapp_notification_example(template.name)
        
        print("\n🎉 Example completed successfully!")
        print("\n📋 Summary:")
        print(f"   Template: {template.name if template else 'Not created'}")
        print(f"   Message: {message.name if message else 'Not sent'}")
        print(f"   Notification: {notification.name if notification else 'Not created'}")
        
        print("\n💡 Next Steps:")
        print("   1. Check template status in WhatsApp Templates")
        print("   2. Wait for template approval from Meta")
        print("   3. Test sending messages with approved template")
        print("   4. Set up notifications for automated sending")
        
    except Exception as e:
        print(f"❌ Example failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 