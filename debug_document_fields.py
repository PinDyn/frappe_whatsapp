#!/usr/bin/env python3
"""
Debug script to check what fields are available in a document for dynamic field replacement.
"""

import frappe

def debug_document_fields(doctype, docname):
    """Debug what fields are available in a document."""
    
    try:
        # Get the document
        doc = frappe.get_doc(doctype, docname)
        
        # Get document as dict
        doc_data = doc.as_dict()
        
        print(f"🔍 Debugging Document: {doctype} - {docname}")
        print("=" * 50)
        
        print(f"📄 Document Name: {doc.name}")
        print(f"📋 Document Type: {doc.doctype}")
        
        print("\n📊 All Available Fields:")
        print("-" * 30)
        for key, value in doc_data.items():
            print(f"  {key}: {value}")
        
        print(f"\n🔑 Key Fields:")
        print(f"  name: {doc_data.get('name', 'NOT FOUND')}")
        print(f"  doctype: {doc_data.get('doctype', 'NOT FOUND')}")
        
        # Test dynamic replacement
        print(f"\n🧪 Testing Dynamic Replacement:")
        test_template = "{{name}}_metal"
        print(f"  Template: {test_template}")
        
        # Simple replacement test
        if 'name' in doc_data:
            result = test_template.replace("{{name}}", str(doc_data['name']))
            print(f"  Result: {result}")
        else:
            print(f"  ❌ 'name' field not found in document data")
        
        # Test with button utils
        print(f"\n🔧 Testing with Button Utils:")
        from frappe_whatsapp.frappe_whatsapp.utils.button_utils import process_dynamic_payload
        result = process_dynamic_payload(test_template, doc, doc_data)
        print(f"  Button Utils Result: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        frappe.log_error(f"Debug Document Fields Error: {e}")

if __name__ == "__main__":
    # Replace these with your actual doctype and document name
    doctype = "Lead"  # or whatever your doctype is
    docname = "CRM-LEAD-2025-00073"  # or whatever your document name is
    
    debug_document_fields(doctype, docname) 