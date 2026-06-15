frappe.pages['inventory'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Inventory',
		single_column: true
	});

	// Render custom template structure
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
		var tbody = $('#inventory-table-body');
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
					$('#product-count').text('0 products');
				}
			}
		});
	};

	// Render table rows
	var render_table = function(products) {
		var tbody = $('#inventory-table-body');
		tbody.empty();

		$('#product-count').text(`${products.length} products`);

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
	$('#inventory-search').on('keyup input', function() {
		var query = $(this).val().toLowerCase();
		var filtered = all_products.filter(function(p) {
			return p.item_name.toLowerCase().indexOf(query) !== -1 || p.item_code.toLowerCase().indexOf(query) !== -1 || p.brand.toLowerCase().indexOf(query) !== -1;
		});
		render_table(filtered);
	});

	$('#select-all-products').on('change', function() {
		$('.product-select-checkbox').prop('checked', $(this).prop('checked'));
	});

	$('.btn-refresh-catalogue').on('click', function() {
		load_data();
	});

	// Initial Load
	load_data();
};
