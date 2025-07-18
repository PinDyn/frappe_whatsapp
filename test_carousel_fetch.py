#!/usr/bin/env python3
"""
Test Script: Carousel Template Fetching

This script tests the carousel template fetching functionality from Meta.
It fetches templates and verifies that carousel templates are properly parsed.

Usage:
    python test_carousel_fetch.py
"""

import frappe
import json

def test_carousel_fetch():
    """Test carousel template fetching functionality."""
    print("🧪 Testing Carousel Template Fetching")
    print("=" * 50)
    
    try:
        # Call the fetch function
        print("📥 Fetching templates from Meta...")
        from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_templates.whatsapp_templates import fetch
        fetch()
        
        # Check for carousel templates
        print("\n🔍 Checking for carousel templates...")
        carousel_templates = frappe.get_all(
            "WhatsApp Templates",
            filters={"template_type": "Carousel"},
            fields=["name", "template_name", "status", "id"]
        )
        
        print(f"Found {len(carousel_templates)} carousel templates:")
        for template in carousel_templates:
            print(f"   📋 {template.template_name} (ID: {template.id})")
            print(f"      Status: {template.status}")
            
            # Get the full template document
            template_doc = frappe.get_doc("WhatsApp Templates", template.name)
            
            # Check carousel cards
            if hasattr(template_doc, 'carousel_cards') and template_doc.carousel_cards:
                print(f"      Cards: {len(template_doc.carousel_cards)}")
                
                for card in template_doc.carousel_cards:
                    print(f"         Card {card.card_index}:")
                    print(f"            Header: {card.header_type}")
                    if card.header_content:
                        print(f"            Content: {card.header_content[:50]}...")
                    if card.whatsapp_handle:
                        print(f"            Handle: {card.whatsapp_handle[:50]}...")
                    if card.body_text:
                        print(f"            Body: {card.body_text[:50]}...")
                    
                    # Check buttons
                    if hasattr(card, 'buttons') and card.buttons:
                        print(f"            Buttons: {len(card.buttons)}")
                        for button in card.buttons:
                            print(f"               - {button.button_type}: {button.button_text}")
            else:
                print(f"      ❌ No carousel cards found")
        
        return carousel_templates
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return []

def check_template_structure(template_name):
    """Check the structure of a specific template."""
    print(f"\n🔍 Checking template structure: {template_name}")
    print("-" * 40)
    
    try:
        template = frappe.get_doc("WhatsApp Templates", template_name)
        
        print(f"Template Type: {template.template_type}")
        print(f"Status: {template.status}")
        print(f"Meta ID: {template.id}")
        
        if template.template_type == "Carousel":
            print(f"Carousel Cards: {len(template.carousel_cards) if hasattr(template, 'carousel_cards') else 0}")
            
            if hasattr(template, 'carousel_cards') and template.carousel_cards:
                for i, card in enumerate(template.carousel_cards):
                    print(f"\nCard {i+1}:")
                    print(f"  Index: {card.card_index}")
                    print(f"  Header Type: {card.header_type}")
                    print(f"  Header Content: {card.header_content}")
                    print(f"  WhatsApp Handle: {card.whatsapp_handle}")
                    print(f"  Body Text: {card.body_text}")
                    
                    if hasattr(card, 'buttons') and card.buttons:
                        print(f"  Buttons: {len(card.buttons)}")
                        for button in card.buttons:
                            print(f"    - {button.button_type}: {button.button_text}")
            else:
                print("❌ No carousel cards found")
        else:
            print("Not a carousel template")
            
    except Exception as e:
        print(f"❌ Error checking template: {e}")

def main():
    """Main test function."""
    print("🚀 Carousel Template Fetch Test")
    print("=" * 60)
    
    # Check WhatsApp settings first
    try:
        settings = frappe.get_doc("WhatsApp Settings")
        if not all([settings.get_password("token"), settings.app_id, settings.business_id]):
            print("❌ WhatsApp settings not configured properly.")
            return
        print("✅ WhatsApp settings configured")
    except Exception as e:
        print(f"❌ Error checking settings: {e}")
        return
    
    print("\n" + "=" * 60)
    
    # Run the fetch test
    carousel_templates = test_carousel_fetch()
    
    if carousel_templates:
        print(f"\n🎉 Fetch test completed!")
        print(f"Found {len(carousel_templates)} carousel templates")
        
        # Check structure of first carousel template
        if carousel_templates:
            first_template = carousel_templates[0]
            check_template_structure(first_template.name)
    else:
        print("\n⚠️  No carousel templates found")
        print("This might be expected if no carousel templates exist in Meta")
    
    print("\n💡 Next Steps:")
    print("   1. Check the templates in WhatsApp Templates list")
    print("   2. Verify carousel cards are properly loaded")
    print("   3. Test sending messages with the templates")

if __name__ == "__main__":
    main() 