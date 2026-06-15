frappe.pages['orders_page'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Orders',
		single_column: true
	});

	// Trigger the shared global orders renderer
	frappe.require("/assets/erpops/css/inventory_page.css", function() {
		window.render_erpops_orders(wrapper);
	});
};
