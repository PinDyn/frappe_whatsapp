#!/usr/bin/env python3
"""
Test script to verify the correct import path for carousel_utils
"""

import sys
import os

# Add the frappe_whatsapp path to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'frappe_whatsapp'))

try:
    # Test different import paths
    print("Testing import paths...")
    
    # Test 1: Direct import
    try:
        from frappe_whatsapp.frappe_whatsapp.utils.carousel_utils import validate_carousel_template
        print("✅ Direct import works: from frappe_whatsapp.frappe_whatsapp.utils.carousel_utils")
    except ImportError as e:
        print(f"❌ Direct import failed: {e}")
    
    # Test 2: Relative import from doctype
    try:
        import frappe_whatsapp.frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_templates.whatsapp_templates
        print("✅ Module import works")
    except ImportError as e:
        print(f"❌ Module import failed: {e}")
    
    # Test 3: Check if utils directory is accessible
    utils_path = os.path.join(os.path.dirname(__file__), 'frappe_whatsapp', 'frappe_whatsapp', 'frappe_whatsapp', 'utils')
    if os.path.exists(utils_path):
        print(f"✅ Utils directory exists: {utils_path}")
        if os.path.exists(os.path.join(utils_path, 'carousel_utils.py')):
            print("✅ carousel_utils.py exists")
        else:
            print("❌ carousel_utils.py not found")
    else:
        print(f"❌ Utils directory not found: {utils_path}")
    
except Exception as e:
    print(f"❌ Test failed: {e}") 