/* Global client script for ErpOps custom route interception */

$(document).ready(function() {
    console.log("Alaiy OS Global Router loaded.");
    
    var check_and_redirect = function() {
        if (typeof frappe !== 'undefined' && typeof frappe.get_route_str === 'function') {
            var route = frappe.get_route_str() || "";
            var route_lower = route.toLowerCase();
            
            if (route_lower === 'inventory' || 
                route_lower === 'workspaces/inventory' || 
                route_lower === 'workspace/inventory' || 
                route_lower === 'workspaces/inventory ws' ||
                route_lower === 'workspace/inventory ws') {
                
                console.log("Redirecting to inventory_page...");
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
