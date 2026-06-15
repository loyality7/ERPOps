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

				<!-- Pagination Footer -->
				<div class="inventory-card-footer" style="display: flex; justify-content: space-between; align-items: center; padding: 14px 24px; border-top: 1px solid #f1f5f9; background: #fafbfd;">
					<div class="text-muted" style="font-size: 13px;">
						Showing <span id="pagination-start">0</span> to <span id="pagination-end">0</span> of <span id="pagination-total">0</span> products
					</div>
					<div style="display: flex; gap: 8px;">
						<button class="btn btn-default btn-xs btn-prev-page" style="padding: 5px 10px; font-weight: 500;"><i class="fa fa-chevron-left"></i> Previous</button>
						<button class="btn btn-default btn-xs btn-next-page" style="padding: 5px 10px; font-weight: 500;">Next <i class="fa fa-chevron-right"></i></button>
					</div>
				</div>
			</div>
		</div>
    `);

    var all_products = [];
    var displayed_products = [];
    var current_page = 1;
    var page_size = 50;

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
                    current_page = 1;
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
        displayed_products = products;
        var total_products = products.length;
        var total_pages = Math.ceil(total_products / page_size) || 1;
        
        if (current_page > total_pages) current_page = total_pages;
        if (current_page < 1) current_page = 1;

        var start_index = (current_page - 1) * page_size;
        var end_index = Math.min(start_index + page_size, total_products);

        var tbody = $(wrapper).find('#inventory-table-body');
        tbody.empty();

        $(wrapper).find('#product-count').text(`${total_products} products`);
        $(wrapper).find('#pagination-total').text(total_products);
        $(wrapper).find('#pagination-start').text(total_products > 0 ? start_index + 1 : 0);
        $(wrapper).find('#pagination-end').text(end_index);

        if (total_products === 0) {
            tbody.html('<tr><td colspan="8" class="text-center py-4">No matching products found.</td></tr>');
            return;
        }

        var page_products = products.slice(start_index, end_index);

        page_products.forEach(function(p) {
            var status_class = p.shopify_status === 'Synced' ? 'pill-synced' : 'pill-not-synced';
            var status_icon = p.shopify_status === 'Synced' ? '<i class="fa fa-check-circle text-success mr-1"></i>' : '';
            
            var row = $(`
				<tr>
					<td><input type="checkbox" class="product-select-checkbox" data-id="${p.item_code}"></td>
					<td>
						${p.has_variants ? `
							<i class="fa fa-chevron-right text-muted row-chevron" style="font-size: 10px; cursor: pointer;" data-item-code="${p.item_code}"></i>
						` : ''}
					</td>
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

        // Disable/enable pagination buttons
        $(wrapper).find('.btn-prev-page').prop('disabled', current_page === 1);
        $(wrapper).find('.btn-next-page').prop('disabled', current_page === total_pages);
    };

    // Event Handlers
    $(wrapper).find('#inventory-search').on('keyup input', function() {
        var query = $(this).val().toLowerCase();
        var filtered = all_products.filter(function(p) {
            return p.item_name.toLowerCase().indexOf(query) !== -1 || p.item_code.toLowerCase().indexOf(query) !== -1 || p.brand.toLowerCase().indexOf(query) !== -1;
        });
        current_page = 1;
        render_table(filtered);
    });

    $(wrapper).find('#select-all-products').on('change', function() {
        $(wrapper).find('.product-select-checkbox').prop('checked', $(this).prop('checked'));
    });

    $(wrapper).find('.btn-refresh-catalogue').on('click', function() {
        load_data();
    });

    $(wrapper).find('.btn-prev-page').on('click', function() {
        if (current_page > 1) {
            current_page--;
            render_table(displayed_products);
        }
    });

    $(wrapper).find('.btn-next-page').on('click', function() {
        var total_pages = Math.ceil(displayed_products.length / page_size) || 1;
        if (current_page < total_pages) {
            current_page++;
            render_table(displayed_products);
        }
    });

    // Toggle row variants expansion
    $(wrapper).on('click', '.row-chevron', function() {
        var $icon = $(this);
        var $tr = $icon.closest('tr');
        var item_code = $icon.data('item-code');
        
        if ($icon.hasClass('fa-chevron-right')) {
            $icon.removeClass('fa-chevron-right').addClass('fa-chevron-down');
            
            var $next = $tr.next('.variants-container-row');
            if ($next.length) {
                $next.show();
                return;
            }
            
            var $loadingRow = $(`
                <tr class="variants-container-row loading-variants">
                    <td></td>
                    <td></td>
                    <td colspan="6" class="py-3">
                        <i class="fa fa-spinner fa-spin mr-2"></i> Loading variants...
                    </td>
                </tr>
            `);
            $tr.after($loadingRow);
            
            frappe.call({
                method: 'erpops.erpops.api.get_item_variants',
                args: { item_code: item_code },
                callback: function(r) {
                    $tr.next('.variants-container-row').remove();
                    if (r.message && r.message.length) {
                        var variantsHtml = '';
                        r.message.forEach(function(v) {
                            var status_class = v.shopify_status === 'Synced' ? 'pill-synced' : 'pill-not-synced';
                            var status_icon = v.shopify_status === 'Synced' ? '<i class="fa fa-check-circle text-success mr-1"></i>' : '';
                            
                            variantsHtml += `
                                <div class="variant-item-line d-flex align-items-center justify-content-between py-2 border-bottom" style="gap: 12px;">
                                    <div class="d-flex align-items-center" style="gap: 12px; flex: 1; min-width: 0;">
                                        <img src="${v.image}" class="product-thumb" style="width: 30px; height: 30px; border-radius: 4px; object-fit: cover;" onerror="this.src='/assets/erpops/images/logo.png'">
                                        <div class="product-meta" style="min-width: 0;">
                                            <a href="/app/item/${v.item_code}" class="product-title-link" style="font-size: 13px; font-weight: 600; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${v.item_name}</a>
                                            <span class="product-sku text-muted" style="font-size: 11px; display: block;">${v.item_code}</span>
                                        </div>
                                    </div>
                                    <div style="width: 120px; font-size: 13px; color: #475569; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${v.brand}</div>
                                    <div style="width: 100px; font-weight: bold; font-size: 13px;" class="${v.available > 0 ? 'text-success' : 'text-warning'}">${v.available} available</div>
                                    <div style="width: 100px; font-size: 13px; color: #475569;">${v.on_hand} on hand</div>
                                    <div style="width: 140px; display: flex; align-items: center; justify-content: flex-end;">
                                        <span class="status-pill ${status_class}" style="font-size: 11px; padding: 2px 6px;">${status_icon}${v.shopify_status}</span>
                                        ${v.shopify_id ? `
                                            <a href="https://${frappe.boot.sysdefaults.shopify_domain || 'shopify.com'}/admin/products/${v.shopify_id}" target="_blank" class="status-action-btn ml-2" title="View in Shopify">
                                                <i class="fa fa-external-link text-muted" style="font-size: 11px;"></i>
                                            </a>
                                        ` : ''}
                                    </div>
                                </div>
                            `;
                        });
                        
                        var $variantsRow = $(`
                            <tr class="variants-container-row">
                                <td></td>
                                <td></td>
                                <td colspan="6" class="bg-light p-3" style="border-radius: 4px;">
                                    <div class="variant-list-container pl-3" style="border-left: 2px solid #cbd5e1;">
                                        <div class="text-muted font-weight-bold mb-2" style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">Product Variants</div>
                                        ${variantsHtml}
                                    </div>
                                </td>
                            </tr>
                        `);
                        $tr.after($variantsRow);
                    } else {
                        var $noVariantsRow = $(`
                            <tr class="variants-container-row">
                                <td></td>
                                <td></td>
                                <td colspan="6" class="py-2 text-muted italic pl-4">No variants found.</td>
                            </tr>
                        `);
                        $tr.after($noVariantsRow);
                    }
                }
            });
        } else {
            $icon.removeClass('fa-chevron-down').addClass('fa-chevron-right');
            $tr.next('.variants-container-row').hide();
        }
    });

    // Initial Load
    load_data();
};

window.render_erpops_orders = function(wrapper) {
    if (!wrapper) return;

    // Render layout with only the Sales Orders list
    $(wrapper).find('.layout-main-section').html(`
		<div class="erpops-inventory-container">
			<div class="inventory-card">
				<div class="inventory-card-header">
					<div class="header-left">
						<span class="card-title">Sales Orders</span>
						<span class="badge badge-info" id="orders-count">0 orders</span>
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
    `);

    var orders = [];

    var load_orders = function() {
        var tbody = $(wrapper).find('#orders-table-body');
        tbody.html(`
            <tr>
                <td colspan="8" class="text-center py-4">
                    <i class="fa fa-spinner fa-spin fa-lg text-muted"></i> Loading orders...
                </td>
            </tr>
        `);
        frappe.call({
            method: 'erpops.erpops.api.get_sales_orders',
            callback: function(r) {
                if (r.message) {
                    orders = r.message;
                    render_orders(orders);
                } else {
                    tbody.html('<tr><td colspan="8" class="text-center py-4">No orders found.</td></tr>');
                    $(wrapper).find('#orders-count').text('0 orders');
                }
            }
        });
    };

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
					<td><a class="order-link" data-id="${o.id}" href="/app/sales-order/${o.id}"><b>${o.id}</b></a></td>
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
        load_orders();
    });

    $(wrapper).on('click', '.order-link', function(e) {
        e.preventDefault();
        var id = $(this).attr('data-id');
        frappe.set_route('Form', 'Sales Order', id);
    });

    // Initial populate
    load_orders();
};

window.render_erpops_returns = function(wrapper) {
    if (!wrapper) return;
    $(wrapper).find('.layout-main-section').html(`
        <div class="erpops-inventory-container text-center py-5">
            <p class="text-muted" style="font-size: 14px; margin-top: 24px;">No returns data available.</p>
        </div>
    `);
};

window.render_erpops_analytics = function(wrapper) {
    if (!wrapper) return;
    $(wrapper).find('.layout-main-section').html(`
        <div class="erpops-inventory-container text-center py-5">
            <p class="text-muted" style="font-size: 14px; margin-top: 24px;">No analytics data available.</p>
        </div>
    `);
};

window.render_erpops_channels = function(wrapper) {
    if (!wrapper) return;

    // Render structure
    $(wrapper).find('.layout-main-section').html(`
		<div class="erpops-inventory-container">
			<div class="inventory-header-desc">
				<p class="text-muted">Configure and sync your external e-commerce sales channels.</p>
			</div>
			
			<div class="channels-cards-list" style="max-width: 800px;">
				<!-- Shopify Channel Card -->
				<div class="inventory-card">
					<div class="inventory-card-header">
						<div class="header-left" style="display:flex; align-items:center; gap:8px;">
							<i class="fa fa-shopping-bag text-primary" style="font-size: 20px;"></i>
							<span class="card-title">Shopify Integration</span>
						</div>
						<div class="header-right" style="display:flex; align-items:center; gap:10px;">
							<span style="font-size: 13px; font-weight: 500; color: #64748b;">Status:</span>
							<label class="erpops-switch">
								<input type="checkbox" id="shopify-toggle-enable">
								<span class="erpops-slider round"></span>
							</label>
						</div>
					</div>
					<div style="padding: 24px;">
						<table class="table" style="margin-bottom: 20px; font-size: 13px;">
							<tbody>
								<tr>
									<td style="border-top:none; color:#64748b; width:40%; padding: 8px 0;">Channel Name</td>
									<td style="border-top:none; font-weight:600; padding: 8px 0;">Shopify</td>
								</tr>
								<tr>
									<td style="color:#64748b; padding: 8px 0;">Domain</td>
									<td id="shopify-chan-domain" style="font-weight:600; padding: 8px 0;">Loading...</td>
								</tr>
								<tr>
									<td style="color:#64748b; padding: 8px 0;">Last Sync</td>
									<td id="shopify-chan-sync" class="text-muted" style="padding: 8px 0;">Loading...</td>
								</tr>
							</tbody>
						</table>
						<div style="display: flex; gap: 10px; justify-content: flex-end;">
							<button class="btn btn-default btn-sm btn-shopify-settings"><i class="fa fa-cog"></i> Configure Settings</button>
							<button class="btn btn-primary btn-sm btn-run-sync"><i class="fa fa-refresh"></i> Sync Now</button>
						</div>
					</div>
				</div>
			</div>
		</div>
    `);

    // Fetch and bind
    var load_chan_status = function() {
        frappe.call({
            method: 'erpops.erpops.api.get_shopify_status',
            callback: function(r) {
                if (r.message && r.message.success) {
                    var status = r.message;
                    $(wrapper).find('#shopify-toggle-enable').prop('checked', status.enable_shopify === 1);
                    $(wrapper).find('#shopify-chan-domain').text(status.shopify_url);
                    $(wrapper).find('#shopify-chan-sync').text(status.last_sync || 'Never synced');
                }
            }
        });
    };

    // Toggle event
    $(wrapper).find('#shopify-toggle-enable').on('change', function() {
        var enable = $(this).prop('checked') ? 1 : 0;
        frappe.call({
            method: 'erpops.erpops.api.toggle_shopify_status',
            args: { enable: enable },
            callback: function(r) {
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: __('Shopify integration ' + (enable ? 'Enabled' : 'Disabled')),
                        indicator: enable ? 'green' : 'red'
                    });
                } else {
                    frappe.msgprint(__('Failed to update Shopify status.'));
                }
            }
        });
    });

    // Configure settings redirection
    $(wrapper).find('.btn-shopify-settings').on('click', function() {
        frappe.set_route('Form', 'Shopify Setting');
    });

    // Sync now action
    $(wrapper).find('.btn-run-sync').on('click', function() {
        var $btn = $(this);
        var original_html = $btn.html();
        $btn.prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> Syncing...');
        frappe.call({
            method: 'erpops.erpops.api.run_manual_sync',
            callback: function(r) {
                $btn.prop('disabled', false).html(original_html);
                frappe.show_alert({
                    message: __('Sync executed successfully'),
                    indicator: 'green'
                });
                load_chan_status();
            }
        });
    });

    // Load initial
    load_chan_status();
};

window.render_erpops_channels_overview = function(wrapper) {
    if (!wrapper) return;

    $(wrapper).find('.layout-main-section').html(`
		<div class="erpops-inventory-container">
			<div class="inventory-header-desc">
				<p class="text-muted">Manage your external e-commerce integrations and sales channels.</p>
			</div>
			
			<div class="channels-cards-list" style="max-width: 800px;">
				<!-- Shopify Integration Row -->
				<div class="inventory-card" style="cursor: pointer; margin-bottom: 20px;" onclick="frappe.set_route('Form', 'Shopify Setting')">
					<div style="padding: 24px; display: flex; justify-content: space-between; align-items: center;">
						<div style="display: flex; align-items: center; gap: 15px;">
							<i class="fa fa-shopping-bag text-primary" style="font-size: 24px;"></i>
							<div>
								<h4 style="margin: 0 0 4px 0; font-weight: 600;">Shopify</h4>
								<span id="shopify-overview-status" class="text-muted" style="font-size: 13px;">Checking status...</span>
							</div>
						</div>
						<i class="fa fa-chevron-right text-muted"></i>
					</div>
				</div>
				
				<!-- Amazon Integration Row (Coming Soon) -->
				<div class="inventory-card" style="margin-bottom: 20px; opacity: 0.6;">
					<div style="padding: 24px; display: flex; justify-content: space-between; align-items: center;">
						<div style="display: flex; align-items: center; gap: 15px;">
							<i class="fa fa-amazon text-warning" style="font-size: 24px;"></i>
							<div>
								<h4 style="margin: 0 0 4px 0; font-weight: 600; color: #475569;">Amazon</h4>
								<span class="text-muted" style="font-size: 13px;">Coming soon</span>
							</div>
						</div>
						<i class="fa fa-lock text-muted"></i>
					</div>
				</div>
			</div>
		</div>
    `);

    // Fetch and populate overview status
    frappe.call({
        method: 'erpops.erpops.api.get_shopify_status',
        callback: function(r) {
            if (r.message && r.message.success) {
                var status = r.message;
                var text = status.enable_shopify === 1 ? 'Connected to ' + status.shopify_url : 'Disconnected';
                var color = status.enable_shopify === 1 ? '#10b981' : '#ef4444';
                $(wrapper).find('#shopify-overview-status')
                    .html(`<span style="color: ${color}; font-weight: 600;">${text}</span>`);
            }
        }
    });
};

$(document).ready(function() {
    console.log("Alaiy OS Global Router loaded.");
    
    var check_and_render = function() {
        if (window.erpops_route_interval) {
            clearInterval(window.erpops_route_interval);
            window.erpops_route_interval = null;
        }

        if (typeof frappe !== 'undefined' && typeof frappe.get_route_str === 'function') {
            var route = frappe.get_route_str() || "";
            var route_lower = route.toLowerCase();
            console.log("[Alaiy OS Router] Current Route:", route_lower);
            
            if (route_lower === 'workspaces/inventory' || 
                route_lower === 'workspace/inventory' || 
                route_lower === 'inventory') {
                
                var attempts = 0;
                window.erpops_route_interval = setInterval(function() {
                    attempts++;
                    var wrapper = $('.page-container:visible')[0];
                    console.log("[Alaiy OS Router] Checking Inventory wrapper, attempt:", attempts, "Wrapper:", wrapper ? "found" : "null");
                    if (wrapper && $(wrapper).find('.layout-main-section').length > 0) {
                        clearInterval(window.erpops_route_interval);
                        console.log("[Alaiy OS Router] Found main layout section!");
                        if ($(wrapper).find('.erpops-inventory-container').length === 0) {
                            console.log("Injecting custom Product Catalogue into Workspace layout...");
                            frappe.require("/assets/erpops/css/inventory_page.css", function() {
                                window.render_erpops_inventory(wrapper);
                            });
                        }
                    }
                    if (attempts > 50) {
                        clearInterval(window.erpops_route_interval);
                    }
                }, 100);
                
            } else if (route_lower === 'workspaces/orders' || 
                       route_lower === 'workspace/orders' || 
                       route_lower === 'orders') {
                
                var attempts = 0;
                window.erpops_route_interval = setInterval(function() {
                    attempts++;
                    var wrapper = $('.page-container:visible')[0];
                    console.log("[Alaiy OS Router] Checking Orders wrapper, attempt:", attempts, "Wrapper:", wrapper ? "found" : "null");
                    if (wrapper && $(wrapper).find('.layout-main-section').length > 0) {
                        clearInterval(window.erpops_route_interval);
                        console.log("[Alaiy OS Router] Found main layout section!");
                        if ($(wrapper).find('.erpops-tabs-header').length === 0) {
                            console.log("Injecting custom Orders & Returns panel into Workspace layout...");
                            frappe.require("/assets/erpops/css/inventory_page.css", function() {
                                window.render_erpops_orders(wrapper);
                            });
                        }
                    }
                    if (attempts > 50) {
                        clearInterval(window.erpops_route_interval);
                    }
                }, 100);
            } else if (route_lower === 'workspaces/channels' || 
                       route_lower === 'workspace/channels' || 
                       route_lower === 'channels') {
                
                var attempts = 0;
                window.erpops_route_interval = setInterval(function() {
                    attempts++;
                    var wrapper = $('.page-container:visible')[0];
                    console.log("[Alaiy OS Router] Checking Channels wrapper, attempt:", attempts, "Wrapper:", wrapper ? "found" : "null");
                    if (wrapper && $(wrapper).find('.layout-main-section').length > 0) {
                        clearInterval(window.erpops_route_interval);
                        console.log("[Alaiy OS Router] Found main layout section!");
                        if ($(wrapper).find('#shopify-overview-status').length === 0) {
                            console.log("Injecting custom Channels panel into Workspace layout...");
                            frappe.require("/assets/erpops/css/inventory_page.css", function() {
                                window.render_erpops_channels_overview(wrapper);
                            });
                        }
                    }
                    if (attempts > 50) {
                        clearInterval(window.erpops_route_interval);
                    }
                }, 100);
            } else if (route_lower === 'workspaces/shopify' || 
                       route_lower === 'workspace/shopify' || 
                       route_lower === 'shopify') {
                
                var attempts = 0;
                window.erpops_route_interval = setInterval(function() {
                    attempts++;
                    var wrapper = $('.page-container:visible')[0];
                    console.log("[Alaiy OS Router] Checking Shopify wrapper, attempt:", attempts, "Wrapper:", wrapper ? "found" : "null");
                    if (wrapper && $(wrapper).find('.layout-main-section').length > 0) {
                        clearInterval(window.erpops_route_interval);
                        console.log("[Alaiy OS Router] Found main layout section!");
                        if ($(wrapper).find('#shopify-toggle-enable').length === 0) {
                            console.log("Injecting custom Shopify details panel into Workspace layout...");
                            frappe.require("/assets/erpops/css/inventory_page.css", function() {
                                window.render_erpops_channels(wrapper);
                            });
                        }
                    }
                    if (attempts > 50) {
                        clearInterval(window.erpops_route_interval);
                    }
                }, 100);
            } else if (route_lower === 'workspaces/returns' || 
                       route_lower === 'workspace/returns' || 
                       route_lower === 'returns') {
                
                var attempts = 0;
                window.erpops_route_interval = setInterval(function() {
                    attempts++;
                    var wrapper = $('.page-container:visible')[0];
                    console.log("[Alaiy OS Router] Checking Returns wrapper, attempt:", attempts, "Wrapper:", wrapper ? "found" : "null");
                    if (wrapper && $(wrapper).find('.layout-main-section').length > 0) {
                        clearInterval(window.erpops_route_interval);
                        console.log("[Alaiy OS Router] Found main layout section!");
                        if ($(wrapper).find('#returns-table-body').length === 0) {
                            console.log("Injecting custom Returns panel into Workspace layout...");
                            frappe.require("/assets/erpops/css/inventory_page.css", function() {
                                window.render_erpops_returns(wrapper);
                            });
                        }
                    }
                    if (attempts > 50) {
                        clearInterval(window.erpops_route_interval);
                    }
                }, 100);
            } else if (route_lower === 'workspaces/analytics' || 
                       route_lower === 'workspace/analytics' || 
                       route_lower === 'analytics') {
                
                var attempts = 0;
                window.erpops_route_interval = setInterval(function() {
                    attempts++;
                    var wrapper = $('.page-container:visible')[0];
                    console.log("[Alaiy OS Router] Checking Analytics wrapper, attempt:", attempts, "Wrapper:", wrapper ? "found" : "null");
                    if (wrapper && $(wrapper).find('.layout-main-section').length > 0) {
                        clearInterval(window.erpops_route_interval);
                        console.log("[Alaiy OS Router] Found main layout section!");
                        if ($(wrapper).find('.analytics-grid').length === 0) {
                            console.log("Injecting custom Analytics panel into Workspace layout...");
                            frappe.require("/assets/erpops/css/inventory_page.css", function() {
                                window.render_erpops_analytics(wrapper);
                            });
                        }
                    }
                    if (attempts > 50) {
                        clearInterval(window.erpops_route_interval);
                    }
                }, 100);
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
