/* Global client script for ErpOps custom route interception and inline rendering */

window.render_erpops_inventory = function(wrapper) {
    if (!wrapper) return;
    
    // Render custom template structure inside workspace's main section
    $(wrapper).find('.layout-main-section').html(`
		<div class="erpops-inventory-container">
			<div class="inventory-header-desc">
				<p class="text-muted">Full product catalogue — every SKU across all suppliers and channels.</p>
			</div>

			<div class="inventory-card">
				<div class="inventory-card-header">
					<div class="header-left">
						<span class="card-title">Product Catalogue</span>
						<span class="badge badge-info" id="product-count">0 products</span>
					</div>
					<div class="header-right">
						<div class="search-box-container">
							<input type="text" class="form-control" id="inventory-search" placeholder="Search products...">
							<i class="fa fa-search search-icon"></i>
						</div>
						<button class="btn btn-default btn-sm btn-refresh-catalogue"><i class="fa fa-refresh"></i></button>
						<button class="btn btn-default btn-sm"><i class="fa fa-columns"></i> Columns</button>
						<button class="btn btn-default btn-sm"><i class="fa fa-download"></i> Export</button>
					</div>
				</div>

				<div class="inventory-table-responsive">
					<table class="table erpops-custom-table">
						<thead>
							<tr>
								<th width="40"><input type="checkbox" id="select-all-products"></th>
								<th width="30"></th>
								<th>PRODUCT</th>
								<th>BRAND</th>
								<th>VARIANTS</th>
								<th>AVAILABLE</th>
								<th>ON HAND</th>
								<th>SHOPIFY</th>
							</tr>
						</thead>
						<tbody id="inventory-table-body">
							<tr>
								<td colspan="8" class="text-center py-5">
									<i class="fa fa-spinner fa-spin fa-2x text-muted"></i>
									<p class="mt-2 text-muted">Loading product catalogue...</p>
								</td>
							</tr>
						</tbody>
					</table>
				</div>
			</div>
		</div>
    `);

    var all_products = [];

    // Fetch data from API
    var load_data = function() {
        var tbody = $(wrapper).find('#inventory-table-body');
        tbody.html(`
			<tr>
				<td colspan="8" class="text-center py-5">
					<i class="fa fa-spinner fa-spin fa-2x text-muted"></i>
					<p class="mt-2 text-muted">Loading product catalogue...</p>
				</td>
			</tr>
        `);

        frappe.call({
            method: 'erpops.erpops.api.get_product_catalogue',
            callback: function(r) {
                if (r.message) {
                    all_products = r.message;
                    render_table(all_products);
                } else {
                    tbody.html('<tr><td colspan="8" class="text-center py-4">No products found.</td></tr>');
                    $(wrapper).find('#product-count').text('0 products');
                }
            }
        });
    };

    // Render table rows
    var render_table = function(products) {
        var tbody = $(wrapper).find('#inventory-table-body');
        tbody.empty();

        $(wrapper).find('#product-count').text(`${products.length} products`);

        if (products.length === 0) {
            tbody.html('<tr><td colspan="8" class="text-center py-4">No matching products found.</td></tr>');
            return;
        }

        products.forEach(function(p) {
            var status_class = p.shopify_status === 'Synced' ? 'pill-synced' : 'pill-not-synced';
            var status_icon = p.shopify_status === 'Synced' ? '<i class="fa fa-check-circle text-success mr-1"></i>' : '';
            
            var row = $(`
				<tr>
					<td><input type="checkbox" class="product-select-checkbox" data-id="${p.item_code}"></td>
					<td><i class="fa fa-chevron-right text-muted row-chevron" style="font-size: 10px; cursor: pointer;"></i></td>
					<td class="product-cell">
						<img src="${p.image}" class="product-thumb" onerror="this.src='/assets/erpops/images/logo.png'">
						<div class="product-meta">
							<a href="/app/item/${p.item_code}" class="product-title-link"><b>${p.item_name}</b></a>
							<span class="product-sku text-muted">${p.item_code}</span>
						</div>
					</td>
					<td class="align-middle">${p.brand}</td>
					<td class="align-middle">${p.variants}</td>
					<td class="align-middle font-weight-bold ${p.available > 0 ? 'text-success' : 'text-warning'}">${p.available}</td>
					<td class="align-middle">${p.on_hand}</td>
					<td class="align-middle">
						<div class="shopify-status-cell">
							<span class="status-pill ${status_class}">${status_icon}${p.shopify_status}</span>
							${p.shopify_id ? `
								<a href="https://${frappe.boot.sysdefaults.shopify_domain || 'shopify.com'}/admin/products/${p.shopify_id}" target="_blank" class="status-action-btn ml-2" title="View in Shopify">
									<i class="fa fa-external-link text-muted"></i>
								</a>
							` : `
								<button class="btn btn-default btn-xs status-action-btn ml-2" title="Not Synced">
									<i class="fa fa-eye-slash text-muted"></i>
								</button>
							`}
						</div>
					</td>
				</tr>
            `);
            tbody.append(row);
        });
    };

    // Event Handlers
    $(wrapper).find('#inventory-search').on('keyup input', function() {
        var query = $(this).val().toLowerCase();
        var filtered = all_products.filter(function(p) {
            return p.item_name.toLowerCase().indexOf(query) !== -1 || p.item_code.toLowerCase().indexOf(query) !== -1 || p.brand.toLowerCase().indexOf(query) !== -1;
        });
        render_table(filtered);
    });

    $(wrapper).find('#select-all-products').on('change', function() {
        $(wrapper).find('.product-select-checkbox').prop('checked', $(this).prop('checked'));
    });

    $(wrapper).find('.btn-refresh-catalogue').on('click', function() {
        load_data();
    });

    // Initial Load
    load_data();
};

window.render_erpops_orders = function(wrapper) {
    if (!wrapper) return;

    // Render tab structure and layout
    $(wrapper).find('.layout-main-section').html(`
		<div class="erpops-inventory-container">
			<!-- Custom Tabs Header -->
			<div class="erpops-tabs-header">
				<button class="erpops-tab-btn active" data-tab="orders">Orders</button>
				<button class="erpops-tab-btn" data-tab="returns">Returns</button>
				<button class="erpops-tab-btn" data-tab="analytics">Analytics</button>
			</div>

			<!-- Tab 1: Orders Content -->
			<div class="erpops-tab-content active" id="tab-orders-content">
				<div class="inventory-card">
					<div class="inventory-card-header">
						<div class="header-left">
							<span class="card-title">Sales Orders</span>
							<span class="badge badge-info" id="orders-count">4 orders</span>
						</div>
						<div class="header-right">
							<div class="search-box-container">
								<input type="text" class="form-control" id="orders-search" placeholder="Search orders...">
								<i class="fa fa-search search-icon"></i>
							</div>
							<button class="btn btn-default btn-sm btn-refresh-orders"><i class="fa fa-refresh"></i></button>
							<button class="btn btn-default btn-sm"><i class="fa fa-columns"></i> Columns</button>
							<button class="btn btn-default btn-sm"><i class="fa fa-download"></i> Export</button>
						</div>
					</div>

					<div class="inventory-table-responsive">
						<table class="table erpops-custom-table">
							<thead>
								<tr>
									<th width="40"><input type="checkbox" id="select-all-orders"></th>
									<th>ORDER ID</th>
									<th>CUSTOMER</th>
									<th>DATE</th>
									<th>TOTAL</th>
									<th>PAYMENT STATUS</th>
									<th>FULFILLMENT</th>
									<th>CHANNEL</th>
								</tr>
							</thead>
							<tbody id="orders-table-body">
								<!-- Dynamically populated -->
							</tbody>
						</table>
					</div>
				</div>
			</div>

			<!-- Tab 2: Returns Content -->
			<div class="erpops-tab-content" id="tab-returns-content">
				<div class="inventory-card">
					<div class="inventory-card-header">
						<div class="header-left">
							<span class="card-title">Order Returns</span>
							<span class="badge badge-info" id="returns-count">2 returns</span>
						</div>
						<div class="header-right">
							<button class="btn btn-default btn-sm"><i class="fa fa-refresh"></i></button>
							<button class="btn btn-default btn-sm"><i class="fa fa-download"></i> Export</button>
						</div>
					</div>

					<div class="inventory-table-responsive">
						<table class="table erpops-custom-table">
							<thead>
								<tr>
									<th>RETURN ID</th>
									<th>ORDER ID</th>
									<th>PRODUCT</th>
									<th>REFUND AMOUNT</th>
									<th>REASON</th>
									<th>STATUS</th>
								</tr>
							</thead>
							<tbody id="returns-table-body">
								<!-- Dynamically populated -->
							</tbody>
						</table>
					</div>
				</div>
			</div>

			<!-- Tab 3: Analytics Content -->
			<div class="erpops-tab-content" id="tab-analytics-content">
				<!-- KPI Cards -->
				<div class="analytics-grid">
					<div class="analytics-card">
						<div class="card-metric-label">Sales Today</div>
						<div class="card-metric-value">₹1,245.00</div>
						<div class="card-metric-trend trend-up"><i class="fa fa-arrow-up"></i> +12.4% vs yesterday</div>
					</div>
					<div class="analytics-card">
						<div class="card-metric-label">Total Orders</div>
						<div class="card-metric-value">14</div>
						<div class="card-metric-trend trend-up"><i class="fa fa-arrow-up"></i> +8.3% vs last week</div>
					</div>
					<div class="analytics-card">
						<div class="card-metric-label">Return Rate</div>
						<div class="card-metric-value">2.1%</div>
						<div class="card-metric-trend trend-down"><i class="fa fa-arrow-down"></i> -0.4% this month</div>
					</div>
					<div class="analytics-card">
						<div class="card-metric-label">Avg Order Value</div>
						<div class="card-metric-value">₹88.92</div>
						<div class="card-metric-trend trend-up"><i class="fa fa-arrow-up"></i> +4.1% overall</div>
					</div>
				</div>

				<!-- Visual analytics graphs & progress bars -->
				<div class="row">
					<div class="col-md-6">
						<div class="inventory-card">
							<div class="inventory-card-header">
								<span class="card-title">Sales By Channel</span>
							</div>
							<div style="padding: 24px;">
								<div class="progress-list-item">
									<div class="progress-list-label">
										<span>Shopify Store</span>
										<span><b>₹845.00 (68%)</b></span>
									</div>
									<div class="progress-bar-bg">
										<div class="progress-bar-fill" style="width: 68%; background-color: #3b82f6;"></div>
									</div>
								</div>
								<div class="progress-list-item">
									<div class="progress-list-label">
										<span>Wholesale / B2B</span>
										<span><b>₹300.00 (24%)</b></span>
									</div>
									<div class="progress-bar-bg">
										<div class="progress-bar-fill" style="width: 24%; background-color: #10b981;"></div>
									</div>
								</div>
								<div class="progress-list-item">
									<div class="progress-list-label">
										<span>Retail / POS</span>
										<span><b>₹100.00 (8%)</b></span>
									</div>
									<div class="progress-bar-bg">
										<div class="progress-bar-fill" style="width: 8%; background-color: #f59e0b;"></div>
									</div>
								</div>
							</div>
						</div>
					</div>
					
					<div class="col-md-6">
						<div class="inventory-card">
							<div class="inventory-card-header">
								<span class="card-title">Common Return Reasons</span>
							</div>
							<div style="padding: 24px;">
								<div class="progress-list-item">
									<div class="progress-list-label">
										<span>Size Too Large / Small</span>
										<span><b>62%</b></span>
									</div>
									<div class="progress-bar-bg">
										<div class="progress-bar-fill" style="width: 62%; background-color: #ec4899;"></div>
									</div>
								</div>
								<div class="progress-list-item">
									<div class="progress-list-label">
										<span>Incorrect Item Shipped</span>
										<span><b>23%</b></span>
									</div>
									<div class="progress-bar-bg">
										<div class="progress-bar-fill" style="width: 23%; background-color: #8b5cf6;"></div>
									</div>
								</div>
								<div class="progress-list-item">
									<div class="progress-list-label">
										<span>Fabric Defect / Damaged</span>
										<span><b>15%</b></span>
									</div>
									<div class="progress-bar-bg">
										<div class="progress-bar-fill" style="width: 15%; background-color: #64748b;"></div>
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
    `);

    // Realistic dummy data
    var orders = [
        { id: "ORD-1001", customer: "John Doe", date: "2026-06-15", total: "₹150.00", payment: "Paid", fulfillment: "Fulfilled", channel: "Shopify" },
        { id: "ORD-1002", customer: "Jane Smith", date: "2026-06-15", total: "₹89.50", payment: "Paid", fulfillment: "Processing", channel: "Shopify" },
        { id: "ORD-1003", customer: "Bob Johnson", date: "2026-06-14", total: "₹240.00", payment: "Unpaid", fulfillment: "Processing", channel: "Wholesale" },
        { id: "ORD-1004", customer: "Alice Williams", date: "2026-06-13", total: "₹120.00", payment: "Paid", fulfillment: "Returned", channel: "Shopify" }
    ];

    var returns = [
        { id: "RET-1001", order_id: "ORD-1004", product: "Alaiy Premium Hoodie", amount: "₹120.00", reason: "Size too large", status: "Approved" },
        { id: "RET-1002", order_id: "ORD-0995", product: "Alaiy Tee Cream", amount: "₹45.00", reason: "Fabric defect", status: "Pending" }
    ];

    // Render tables
    var render_orders = function(list) {
        var tbody = $(wrapper).find('#orders-table-body');
        tbody.empty();
        $(wrapper).find('#orders-count').text(`${list.length} orders`);

        list.forEach(function(o) {
            var pay_class = o.payment === 'Paid' ? 'pill-paid' : 'pill-unpaid';
            var ful_class = 'pill-processing';
            if (o.fulfillment === 'Fulfilled') ful_class = 'pill-fulfilled';
            else if (o.fulfillment === 'Returned') ful_class = 'pill-returned';

            tbody.append(`
				<tr>
					<td><input type="checkbox" class="order-select-checkbox"></td>
					<td><a href="#Form/Sales Order/${o.id}"><b>${o.id}</b></a></td>
					<td>${o.customer}</td>
					<td>${o.date}</td>
					<td><b>${o.total}</b></td>
					<td><span class="status-pill ${pay_class}">${o.payment}</span></td>
					<td><span class="status-pill ${ful_class}">${o.fulfillment}</span></td>
					<td><span class="badge" style="background:#f1f5f9; color:#475569;">${o.channel}</span></td>
				</tr>
            `);
        });
    };

    var render_returns = function() {
        var tbody = $(wrapper).find('#returns-table-body');
        tbody.empty();
        $(wrapper).find('#returns-count').text(`${returns.length} returns`);

        returns.forEach(function(r) {
            var status_class = r.status === 'Approved' ? 'pill-paid' : 'pill-processing';
            tbody.append(`
				<tr>
					<td><b>${r.id}</b></td>
					<td><a href="#Form/Sales Order/${r.order_id}"><b>${r.order_id}</b></a></td>
					<td>${r.product}</td>
					<td><b>${r.amount}</b></td>
					<td class="text-muted">${r.reason}</td>
					<td><span class="status-pill ${status_class}">${r.status}</span></td>
				</tr>
            `);
        });
    };

    // Tab switcher
    $(wrapper).find('.erpops-tab-btn').on('click', function() {
        var tab_id = $(this).data('tab');
        $(wrapper).find('.erpops-tab-btn').removeClass('active');
        $(this).addClass('active');
        $(wrapper).find('.erpops-tab-content').removeClass('active');
        $(wrapper).find('#tab-' + tab_id + '-content').addClass('active');
    });

    // Search filter for orders
    $(wrapper).find('#orders-search').on('keyup input', function() {
        var query = $(this).val().toLowerCase();
        var filtered = orders.filter(function(o) {
            return o.id.toLowerCase().indexOf(query) !== -1 || o.customer.toLowerCase().indexOf(query) !== -1 || o.channel.toLowerCase().indexOf(query) !== -1;
        });
        render_orders(filtered);
    });

    $(wrapper).find('#select-all-orders').on('change', function() {
        $(wrapper).find('.order-select-checkbox').prop('checked', $(this).prop('checked'));
    });

    $(wrapper).find('.btn-refresh-orders').on('click', function() {
        render_orders(orders);
    });

    // Initial populate
    render_orders(orders);
    render_returns();
};

$(document).ready(function() {
    console.log("Alaiy OS Global Router loaded.");
    
    var check_and_render = function() {
        if (typeof frappe !== 'undefined' && typeof frappe.get_route_str === 'function') {
            var route = frappe.get_route_str() || "";
            var route_lower = route.toLowerCase();
            
            if (route_lower === 'workspaces/inventory' || 
                route_lower === 'workspace/inventory' || 
                route_lower === 'inventory') {
                
                var wrapper = frappe.container.page.wrapper;
                if (wrapper && $(wrapper).find('.erpops-inventory-container').length === 0) {
                    console.log("Injecting custom Product Catalogue into Workspace layout...");
                    frappe.require("/assets/erpops/css/inventory_page.css", function() {
                        window.render_erpops_inventory(wrapper);
                    });
                }
            } else if (route_lower === 'workspaces/orders' || 
                       route_lower === 'workspace/orders' || 
                       route_lower === 'orders') {
                
                var wrapper = frappe.container.page.wrapper;
                if (wrapper && $(wrapper).find('.erpops-tabs-header').length === 0) {
                    console.log("Injecting custom Orders & Returns panel into Workspace layout...");
                    frappe.require("/assets/erpops/css/inventory_page.css", function() {
                        window.render_erpops_orders(wrapper);
                    });
                }
            }
        }
    };

    if (typeof frappe !== 'undefined' && frappe.router) {
        frappe.router.on('change', check_and_render);
    } else {
        var check_router = setInterval(function() {
            if (typeof frappe !== 'undefined' && frappe.router) {
                clearInterval(check_router);
                frappe.router.on('change', check_and_render);
            }
        }, 100);
    }

    // Run check immediately on load
    setTimeout(check_and_render, 300);
});
