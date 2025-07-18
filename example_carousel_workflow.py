#!/usr/bin/env python3
"""
Example Carousel Workflow for Frappe WhatsApp App

This script demonstrates the complete workflow for creating and sending carousel messages:
1. Upload images to WhatsApp
2. Create a carousel template with the uploaded images
3. Check template status
4. Send carousel message

Usage:
    python example_carousel_workflow.py
"""

import os
import json
import frappe
from integrated_carousel_manager import IntegratedCarouselManager

def create_sample_cards_data(image_handles):
    """
    Create sample cards data for carousel template.
    
    Args:
        image_handles (list): List of image handles from uploads
        
    Returns:
        list: Cards data for template creation
    """
    return [
        {
            "image_handle": image_handles[0] if len(image_handles) > 0 else None,
            "body_text": "Welcome to our amazing product! 🚀",
            "buttons": [
                {
                    "type": "quick_reply",
                    "text": "Learn More",
                    "payload": "learn_more_1"
                },
                {
                    "type": "url",
                    "text": "Visit Website",
                    "url": "https://example.com"
                }
            ]
        },
        {
            "image_handle": image_handles[1] if len(image_handles) > 1 else None,
            "body_text": "Discover amazing features that will transform your experience! ✨",
            "buttons": [
                {
                    "type": "quick_reply",
                    "text": "Get Started",
                    "payload": "get_started_2"
                }
            ]
        },
        {
            "image_handle": image_handles[2] if len(image_handles) > 2 else None,
            "body_text": "Join thousands of satisfied customers today! 🎉",
            "buttons": [
                {
                    "type": "quick_reply",
                    "text": "Contact Us",
                    "payload": "contact_us_3"
                }
            ]
        }
    ]

def main():
    """Main workflow function."""
    print("🚀 Starting Carousel Workflow Example")
    print("=" * 50)
    
    try:
        # Initialize the carousel manager
        manager = IntegratedCarouselManager()
        
        # Step 1: Upload sample images
        print("\n📤 Step 1: Uploading sample images...")
        
        # Check if we have sample images in the current directory
        sample_images = []
        for filename in ["sample1.jpg", "sample2.jpg", "sample3.jpg"]:
            if os.path.exists(filename):
                sample_images.append(filename)
        
        if not sample_images:
            print("No sample images found. Creating dummy uploads for demonstration...")
            # For demonstration, we'll use placeholder handles
            image_handles = ["dummy_handle_1", "dummy_handle_2", "dummy_handle_3"]
        else:
            image_handles = []
            for image_path in sample_images:
                print(f"Uploading {image_path}...")
                result = manager.upload_media(image_path)
                image_handles.append(result["asset_handle"])
                print(f"✅ Uploaded: {result['asset_handle']}")
        
        # Step 2: Create carousel template
        print("\n📝 Step 2: Creating carousel template...")
        
        template_name = "Sample Carousel Template"
        cards_data = create_sample_cards_data(image_handles)
        
        # Save cards data to file for the manager
        cards_file = "sample_cards.json"
        with open(cards_file, 'w') as f:
            json.dump(cards_data, f, indent=2)
        
        result = manager.create_carousel_template(template_name, cards_data)
        print(f"✅ Template created: {result['template_id']}")
        
        # Step 3: Check template status
        print("\n🔍 Step 3: Checking template status...")
        
        status_result = manager.check_template_status(template_name)
        print(f"✅ Template status: {status_result['status']}")
        
        if status_result['status'] == 'APPROVED':
            # Step 4: Send carousel message (if approved)
            print("\n📱 Step 4: Sending carousel message...")
            
            # Example phone number (replace with actual number for testing)
            test_number = "1234567890"  # Replace with actual number
            
            # Example parameters for template variables
            parameters = {
                "body": ["John", "Premium Plan", "50% off"]
            }
            
            send_result = manager.send_carousel_message(template_name, test_number, parameters)
            print(f"✅ Message sent: {send_result['message_id']}")
        else:
            print(f"⚠️  Template not approved yet. Status: {status_result['status']}")
            print("Please wait for approval before sending messages.")
        
        # Step 5: List all uploads and templates
        print("\n📋 Step 5: Summary...")
        manager.list_uploads()
        manager.list_templates()
        
        print("\n🎉 Workflow completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in workflow: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 