/* Global client script for ErpOps custom route interception */

$(document).ready(function() {
    console.log("Alaiy OS Global Router loaded.");
    
    // Add debug banner
    var show_debug = function(msg) {
        var id = "erpops-route-debug-banner";
        var banner = $("#" + id);
        if (banner.length === 0) {
            banner = $("<div id='" + id + "' style='position: fixed; top: 15px; right: 15px; z-index: 9999999; background: #e74c3c; color: white; padding: 10px 15px; border-radius: 8px; font-weight: bold; font-family: sans-serif; box-shadow: 0 4px 6px rgba(0,0,0,0.15); font-size: 13px; pointer-events: none;'></div>");
            $("body").append(banner);
        }
        banner.text("Alaiy OS Route: " + msg);
    };
    
    var check_and_redirect = function() {
        if (typeof frappe !== 'undefined' && typeof frappe.get_route_str === 'function') {
            var route = frappe.get_route_str();
            show_debug(route);
            if (route === 'inventory' || route === 'workspace/Inventory' || route === 'workspace/inventory' || route === 'workspace/Inventory Ws') {
                console.log("Redirecting workspace/Inventory to inventory_page...");
                frappe.set_route('inventory_page');
            }
        } else {
            show_debug("Frappe not ready");
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
