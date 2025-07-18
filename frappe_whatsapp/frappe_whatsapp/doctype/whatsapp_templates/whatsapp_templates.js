// Copyright (c) 2022, Shridhar Patil and contributors
// For license information, please see license.txt

frappe.ui.form.on('WhatsApp Templates', {
	refresh: function(frm) {
		// Add custom buttons
		if (!frm.doc.id) {
			frm.add_custom_button(__('Create Template'), function() {
				frm.call({
					method: 'frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_templates.whatsapp_templates.create_template',
					args: {
						docname: frm.doc.name
					},
					callback: function(r) {
						if (r.exc) {
							frappe.msgprint(__('Error creating template: ') + r.exc);
						} else {
							frm.reload_doc();
						}
					}
				});
			}, __('Actions'));
		} else {
			frm.add_custom_button(__('Update Template'), function() {
				frm.call({
					method: 'frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_templates.whatsapp_templates.update_template_manual',
					args: {
						docname: frm.doc.name
					},
					callback: function(r) {
						if (r.exc) {
							frappe.msgprint(__('Error updating template: ') + r.exc);
						} else {
							frm.reload_doc();
						}
					}
				});
			}, __('Actions'));
		}
	}
});
