/* Global client script for ErpOps custom route interception */

$(document).ready(function() {
    console.log("Alaiy OS Global Router loaded.");
    
    var check_and_redirect = function() {
        if (typeof frappe !== 'undefined' && typeof frappe.get_route_str === 'function') {
            var route = frappe.get_route_str();
            if (route === 'inventory' || route === 'workspace/Inventory' || route === 'workspace/inventory' || route === 'workspace/Inventory Ws') {
                console.log("Redirecting workspace/Inventory to inventory_page...");
                frappe.set_route('inventory_page');
            }
        }
    };

    if (typeof frappe !== 'undefined' && frappe.router) {
        frappe.router.on('change', check_and_redirect);
    } else {
        // Fallback: poll until router is ready
        var check_router = setInterval(function() {
            if (typeof frappe !== 'undefined' && frappe.router) {
                clearInterval(check_router);
                frappe.router.on('change', check_and_redirect);
            }
        }, 100);
    }

    // Run check immediately on load
    setTimeout(check_and_redirect, 300);
});
