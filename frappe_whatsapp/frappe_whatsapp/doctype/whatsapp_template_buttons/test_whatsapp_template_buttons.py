# Copyright (c) 2025, Shridhar Patil and contributors
# For license information, please see license.txt

import frappe
import unittest


class TestWhatsAppTemplateButtons(unittest.TestCase):
    def test_quick_reply_button_validation(self):
        """Test that Quick Reply buttons require payload."""
        doc = frappe.new_doc("WhatsApp Template Buttons")
        doc.button_text = "Test Button"
        doc.button_type = "QUICK_REPLY"
        # Should throw error without payload
        with self.assertRaises(frappe.ValidationError):
            doc.save()

    def test_url_button_validation(self):
        """Test that URL buttons require URL."""
        doc = frappe.new_doc("WhatsApp Template Buttons")
        doc.button_text = "Test Button"
        doc.button_type = "URL"
        # Should throw error without URL
        with self.assertRaises(frappe.ValidationError):
            doc.save()

    def test_phone_number_button_validation(self):
        """Test that Phone Number buttons require phone number."""
        doc = frappe.new_doc("WhatsApp Template Buttons")
        doc.button_text = "Test Button"
        doc.button_type = "PHONE_NUMBER"
        # Should throw error without phone number
        with self.assertRaises(frappe.ValidationError):
            doc.save()

    def test_valid_quick_reply_button(self):
        """Test valid Quick Reply button creation."""
        doc = frappe.new_doc("WhatsApp Template Buttons")
        doc.button_text = "Test Button"
        doc.button_type = "QUICK_REPLY"
        doc.payload = "test_payload"
        # Should save successfully
        doc.save()
        # Clean up
        doc.delete() 