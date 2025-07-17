#!/usr/bin/env python3
"""
Simple test to verify button parameter processing with dynamic field replacement.
"""

import frappe

def test_button_replacement():
    """Test button parameter processing."""
    
    try:
        # Get a test document
        doc = frappe.get_doc("Lead", "CRM-LEAD-2025-00073")
        doc_data = doc.as_dict()
        
        print("🧪 Testing Button Parameter Processing")
        print("=" * 50)
        
        # Test the button utils function directly
        from frappe_whatsapp.frappe_whatsapp.utils.button_utils import process_dynamic_payload
        
        # Test cases
        test_cases = [
            "{{name}}_metal",
            "{{name}}_not-intrested",
            "test123",
            "{{lead_name}}_metal"
        ]
        
        for test_case in test_cases:
            result = process_dynamic_payload(test_case, doc, doc_data)
            print(f"Template: '{test_case}' -> Result: '{result}'")
        
        # Test with mock button parameters
        print("\n🔧 Testing with Mock Button Parameters")
        print("-" * 40)
        
        # Create mock button parameter
        class MockButtonParam:
            def __init__(self, button_type, payload=None, flow_token=None):
                self.button_type = button_type
                self.payload = payload
                self.flow_token = flow_token
                self.button_index = 0
            
            def as_dict(self):
                return {
                    "button_type": self.button_type,
                    "payload": self.payload,
                    "flow_token": self.flow_token,
                    "button_index": self.button_index
                }
        
        # Test FLOW button
        flow_param = MockButtonParam("FLOW", flow_token="{{name}}_metal")
        print(f"FLOW Parameter: {flow_param.as_dict()}")
        
        # Test QUICK_REPLY button
        quick_reply_param = MockButtonParam("QUICK_REPLY", payload="{{name}}_not-intrested")
        print(f"QUICK_REPLY Parameter: {quick_reply_param.as_dict()}")
        
        # Test the full button processing
        from frappe_whatsapp.frappe_whatsapp.utils.button_utils import get_template_buttons_with_dynamic_values
        
        # Create mock template
        class MockTemplate:
            def __init__(self):
                self.buttons = [
                    MockButtonParam("FLOW", flow_token="test"),
                    MockButtonParam("QUICK_REPLY", payload="test")
                ]
        
        template = MockTemplate()
        button_params = [flow_param, quick_reply_param]
        
        result = get_template_buttons_with_dynamic_values(template, button_params, doc, doc_data)
        print(f"\nFinal Button Processing Result: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_button_replacement() 