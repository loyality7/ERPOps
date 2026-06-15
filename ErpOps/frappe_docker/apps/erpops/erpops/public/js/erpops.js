/* Global client script for ErpOps custom route interception */

$(document).on('app_ready', function() {
    frappe.router.on('change', function() {
        var route = frappe.get_route_str();
        if (route === 'inventory' || route === 'workspace/Inventory' || route === 'workspace/inventory' || route === 'workspace/Inventory Ws') {
            frappe.set_route('inventory_page');
        }
    });
    
    // Check initial route on load
    var route = frappe.get_route_str();
    if (route === 'inventory' || route === 'workspace/Inventory' || route === 'workspace/inventory' || route === 'workspace/Inventory Ws') {
        frappe.set_route('inventory_page');
    }
});
