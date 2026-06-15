/* Global client script for ErpOps custom route interception */

frappe.router.on('change', function() {
    var route = frappe.get_route_str();
    if (route === 'inventory' || route === 'workspace/Inventory' || route === 'workspace/inventory' || route === 'workspace/Inventory Ws') {
        frappe.set_route('inventory_page');
    }
});

// Run check immediately on load
$(document).ready(function() {
    setTimeout(function() {
        var route = frappe.get_route_str();
        if (route === 'inventory' || route === 'workspace/Inventory' || route === 'workspace/inventory' || route === 'workspace/Inventory Ws') {
            frappe.set_route('inventory_page');
        }
    }, 300);
});
