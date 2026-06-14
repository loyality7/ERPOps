frappe.pages['erpops_dashboard'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'ErpOps Dashboard',
		single_column: true
	});

	// Main container
	var container = $(wrapper).find(".layout-main-section");
	container.empty();

	// Render dashboard wrapper
	container.html(`
		<div class="erpops-dashboard-wrapper">
			<!-- Shopify Integration Status Card -->
			<div class="erpops-shopify-banner">
				<div class="banner-info">
					<div class="banner-title-row">
						<span class="banner-icon"><i class="fa fa-shopping-bag text-primary"></i></span>
						<span class="banner-title">Shopify Integration Status</span>
						<span id="shopify-status-badge"><span class="label label-default">CHECKING...</span></span>
					</div>
					<div class="banner-meta">
						<span class="meta-item"><i class="fa fa-link"></i> <strong id="shopify-domain-text">Loading...</strong></span>
						<span class="meta-item"><i class="fa fa-clock-o"></i> <span id="shopify-sync-text">Checking last sync...</span></span>
						<span class="meta-item"><i class="fa fa-shopping-cart"></i> <span id="shopify-orders-count">0 orders</span></span>
					</div>
				</div>
				<div class="banner-actions">
				<button class="btn btn-sm btn-success btn-connect-shopify" style="display:none;"><i class="fa fa-plug"></i> Connect Shopify</button>
				<button class="btn btn-sm btn-primary btn-run-sync"><i class="fa fa-refresh"></i> Sync Shopify Now</button>
			</div>
			</div>

			<!-- Header KPI Strip -->
			<div class="erpops-kpi-container">
				<div class="erpops-kpi-card">
					<div class="kpi-label">Sales Today</div>
					<div class="kpi-value" id="kpi-sales">₹0</div>
					<div class="kpi-sub" id="kpi-sales-sub">0 orders</div>
				</div>
				<div class="erpops-kpi-card">
					<div class="kpi-label">Active Alerts</div>
					<div class="kpi-value text-danger" id="kpi-alerts">0</div>
					<div class="kpi-sub" id="kpi-alerts-sub">At risk</div>
				</div>
				<div class="erpops-kpi-card">
					<div class="kpi-label">Warehouse Stock</div>
					<div class="kpi-value" id="kpi-stock">0</div>
					<div class="kpi-sub" id="kpi-stock-sub">0 active SKUs</div>
				</div>
			</div>

			<!-- Main Content Grid -->
			<div class="erpops-main-grid">
				<!-- Left column: Alerts feed -->
				<div class="erpops-grid-col">
					<div class="col-header">
						<h3><i class="fa fa-bell text-danger"></i> Active Operations Feed</h3>
						<button class="btn btn-xs btn-default btn-refresh-alerts"><i class="fa fa-refresh"></i></button>
					</div>
					<div class="erpops-alerts-feed" id="alerts-feed">
						<div class="feed-empty">Loading operations feed...</div>
					</div>
				</div>

				<!-- Right column: Inventory tracker -->
				<div class="erpops-grid-col">
					<div class="col-header">
						<h3><i class="fa fa-cubes text-info"></i> Inventory & Velocity Tracker</h3>
						<button class="btn btn-xs btn-default btn-refresh-inventory"><i class="fa fa-refresh"></i></button>
					</div>
					<div class="erpops-inventory-table-container">
						<table class="table erpops-table">
							<thead>
								<tr>
									<th>SKU</th>
									<th>Stock</th>
									<th>Velocity</th>
									<th>Days Cover</th>
									<th>Status</th>
									<th>Action</th>
								</tr>
							</thead>
							<tbody id="inventory-list">
								<tr><td colspan="6" class="text-center">Loading inventory data...</td></tr>
							</tbody>
						</table>
					</div>
				</div>
			</div>

			<!-- AI Operations Assistant (ask_erpops widget) -->
			<div class="erpops-ai-assistant">
				<div class="ai-header">
					<h4><i class="fa fa-commenting"></i> ErpOps Assistant</h4>
					<div style="display: flex; align-items: center; gap: 8px;">
						<span class="ai-status">Online</span>
						<button class="btn-close-ai ai-close-btn"><i class="fa fa-times"></i></button>
					</div>
				</div>
				<div class="ai-chat-history" id="ai-chat-history">
					<div class="ai-message assistant">
						Hi! I'm your ErpOps Assistant. Ask me anything about revenue, low stock, return rates, or shipment risks.
					</div>
				</div>
				<div class="ai-input-container">
					<input type="text" id="ai-question-input" placeholder="Ask a question (e.g. 'Which SKUs need reorder?')" />
					<button class="btn btn-primary btn-sm btn-ask-ai"><i class="fa fa-paper-plane"></i></button>
				</div>
			</div>

			<!-- Floating AI Trigger Orb -->
			<div class="erpops-ai-trigger">
				<i class="fa fa-comments-o"></i>
			</div>
		</div>
	`);

	// Event Handlers and Refresh Logic
	var refresh_kpi = function() {
		frappe.call({
			method: 'erpops.erpops.api.get_kpi_summary',
			callback: function(r) {
				if (r.message) {
					var kpi = r.message;
					var pct = 0;
					if (kpi.revenue_yesterday) {
						pct = ((kpi.revenue_today - kpi.revenue_yesterday) / kpi.revenue_yesterday) * 100;
					}
					var sign = pct >= 0 ? '+' : '';
					var trend = pct !== 0 ? ` (${sign}${pct.toFixed(1)}% vs yesterday)` : '';
					
					$('#kpi-sales').text(`₹${kpi.revenue_today.toLocaleString('en-IN', {maximumFractionDigits: 0})}`);
					$('#kpi-sales-sub').text(`${kpi.orders_today} orders${trend}`);
					
					$('#kpi-alerts').text(kpi.items_to_action);
					$('#kpi-alerts-sub').text(`${kpi.fires} critical, ${kpi.warns} warning`);
					
					$('#kpi-stock').text(kpi.wh_stock.toLocaleString());
					$('#kpi-stock-sub').text(`${kpi.sku_count} active SKUs`);

					// Update Shopify Status Banner
					if (kpi.shopify_connected) {
						$('#shopify-status-badge').html('<span class="label label-success">CONNECTED</span>');
						$('#shopify-domain-text').text(kpi.shopify_domain);
						$('#shopify-sync-text').text('Last sync: ' + kpi.shopify_last_sync);
						$('#shopify-orders-count').text(kpi.shopify_orders_count + ' synced orders');
						$('.btn-connect-shopify').hide();
						$('.btn-run-sync').show();
					} else {
						$('#shopify-status-badge').html('<span class="label label-danger">DISCONNECTED</span>');
						$('#shopify-domain-text').text('Not Connected');
						$('#shopify-sync-text').text('Click "Connect Shopify" to authorize');
						$('#shopify-orders-count').text('0 synced orders');
						$('.btn-connect-shopify').show();
						$('.btn-run-sync').hide();
					}
				}
			}
		});
	};

	var refresh_alerts = function() {
		var feed = $('#alerts-feed');
		feed.html('<div class="feed-empty"><i class="fa fa-spinner fa-spin"></i> Fetching operations feed...</div>');
		frappe.call({
			method: 'erpops.erpops.api.get_feed_items',
			callback: function(r) {
				feed.empty();
				if (!r.message || r.message.length === 0) {
					feed.html('<div class="feed-empty">No active operational alerts. You are fully caught up!</div>');
					return;
				}
				r.message.forEach(function(alert) {
					var sev_class = alert.severity === 'fire' ? 'border-danger bg-danger-light' : (alert.severity === 'warn' ? 'border-warning bg-warning-light' : 'border-info bg-info-light');
					var badge = alert.severity === 'fire' ? '<span class="label label-danger">CRITICAL</span>' : (alert.severity === 'warn' ? '<span class="label label-warning">WARNING</span>' : '<span class="label label-info">INFO</span>');
					
					var action_html = '';
					if (alert.alert_type === 'Reorder') {
						action_html = `
							<div class="alert-actions">
								<button class="btn btn-xs btn-primary btn-approve-reorder" data-sku="${alert.item_code}" data-qty="50">Approve PO</button>
								<button class="btn btn-xs btn-default btn-snooze-alert" data-id="${alert.name}">Snooze</button>
							</div>
						`;
					} else if (alert.alert_type === 'Late Shipment') {
						action_html = `
							<div class="alert-actions">
								<button class="btn btn-xs btn-success btn-ship-order" data-so="${alert.sales_order}">Mark Shipped</button>
								<button class="btn btn-xs btn-default btn-snooze-alert" data-id="${alert.name}">Snooze</button>
							</div>
						`;
					} else {
						action_html = `
							<div class="alert-actions">
								<button class="btn btn-xs btn-default btn-snooze-alert" data-id="${alert.name}">Dismiss</button>
							</div>
						`;
					}

					var ai_note_html = alert.ai_note ? `<div class="alert-ai-note"><i class="fa fa-magic text-purple"></i> <strong>AI Suggestion:</strong> ${alert.ai_note}</div>` : '';

					feed.append(`
						<div class="alert-card ${sev_class}" data-alert-id="${alert.name}">
							<div class="alert-card-header">
								<span class="alert-title font-weight-bold">${alert.title}</span>
								${badge}
							</div>
							<div class="alert-desc">${alert.description}</div>
							${ai_note_html}
							${action_html}
						</div>
					`);
				});
			}
		});
	};

	var refresh_inventory = function() {
		var list = $('#inventory-list');
		list.html('<tr><td colspan="6" class="text-center"><i class="fa fa-spinner fa-spin"></i> Fetching inventory statuses...</td></tr>');
		frappe.call({
			method: 'erpops.erpops.api.get_inventory_with_velocity',
			callback: function(r) {
				list.empty();
				if (!r.message || r.message.length === 0) {
					list.html('<tr><td colspan="6" class="text-center">No inventory items found.</td></tr>');
					return;
				}
				r.message.forEach(function(item) {
					var status_badge = '';
					if (item.status === 'Healthy') {
						status_badge = '<span class="label label-success">HEALTHY</span>';
					} else if (item.status === 'Reorder') {
						status_badge = '<span class="label label-warning">REORDER</span>';
					} else {
						status_badge = '<span class="label label-danger">LOW</span>';
					}

					var action_btn = '';
					if (item.status !== 'Healthy') {
						action_btn = `<button class="btn btn-xs btn-primary btn-grid-reorder" data-sku="${item.item_code}">Reorder</button>`;
					} else {
						action_btn = `<span class="text-muted">-</span>`;
					}

					var channels = (item.channels && item.channels.length > 0) ? item.channels.join(', ') : 'None';

					list.append(`
						<tr>
							<td class="font-weight-bold">${item.item_code}<br><small class="text-muted">${item.item_name} (${channels})</small></td>
							<td>${item.actual_qty}</td>
							<td>${item.daily_velocity} /day</td>
							<td>${item.days_cover === 999 ? '∞' : item.days_cover + 'd'}</td>
							<td>${status_badge}</td>
							<td>${action_btn}</td>
						</tr>
					`);
				});
			}
		});
	};

	// Ask AI Assistant handler
	var ask_ai = function() {
		var input = $('#ai-question-input');
		var question = input.val().trim();
		if (!question) return;

		var history = $('#ai-chat-history');
		history.append(`<div class="ai-message user">${question}</div>`);
		input.val('');
		history.scrollTop(history[0].scrollHeight);

		frappe.call({
			method: 'erpops.erpops.api.ask_erpops',
			args: { question: question },
			callback: function(r) {
				if (r.message && r.message.answer) {
					history.append(`<div class="ai-message assistant">${r.message.answer.replace(/\n/g, '<br>')}</div>`);
				} else {
					history.append(`<div class="ai-message assistant">Sorry, I couldn't understand that. Please try asking about inventory, stock levels, or revenue.</div>`);
				}
				history.scrollTop(history[0].scrollHeight);
			}
		});
	};

	// Event registrations
	container.on('click', '.btn-refresh-alerts', refresh_alerts);
	container.on('click', '.btn-refresh-inventory', refresh_inventory);
	container.on('click', '.btn-ask-ai', ask_ai);
	container.on('click', '.erpops-ai-trigger', function() {
		$('.erpops-ai-assistant').toggleClass('active');
	});
	container.on('click', '.ai-close-btn', function() {
		$('.erpops-ai-assistant').removeClass('active');
	});
	$('#ai-question-input').on('keypress', function(e) {
		if (e.which === 13) {
			ask_ai();
		}
	});

	// Connect Shopify OAuth click
	container.on('click', '.btn-connect-shopify', function() {
		var btn = $(this);
		btn.prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> Generating link...');
		frappe.call({
			method: 'erpops.erpops.api.get_shopify_connect_url',
			callback: function(r) {
				btn.prop('disabled', false).html('<i class="fa fa-plug"></i> Connect Shopify');
				if (r.message && r.message.url) {
					window.open(r.message.url, '_self');
				} else if (r.message && r.message.error) {
					frappe.msgprint({
						title: 'Shopify Configuration Missing',
						message: r.message.error + '<br><br>Please set <b>SHOPIFY_CLIENT_ID</b> and <b>SHOPIFY_CLIENT_SECRET</b> in your <code>.env</code> file and restart the containers.',
						indicator: 'red'
					});
				} else {
					frappe.msgprint({
						title: 'Error',
						message: 'Could not generate Shopify connect URL. Please check your environment configuration.',
						indicator: 'red'
					});
				}
			}
		});
	});

	// Shopify manual sync click
	container.on('click', '.btn-run-sync', function() {
		var btn = $(this);
		var original_html = btn.html();
		btn.prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> Syncing Shopify...');
		frappe.call({
			method: 'erpops.erpops.api.run_manual_sync',
			callback: function(r) {
				btn.prop('disabled', false).html(original_html);
				frappe.show_alert({message: 'Shopify sync executed successfully.', indicator: 'green'});
				refresh_kpi();
				refresh_alerts();
				refresh_inventory();
			}
		});
	});

	// Inline Feed Actions
	container.on('click', '.btn-approve-reorder, .btn-grid-reorder', function() {
		var sku = $(this).attr('data-sku');
		frappe.prompt([
			{label: 'Item Code', fieldname: 'item_code', fieldtype: 'Data', default: sku, read_only: 1},
			{label: 'Quantity', fieldname: 'qty', fieldtype: 'Float', default: 50, reqd: 1},
			{label: 'Supplier', fieldname: 'supplier', fieldtype: 'Link', options: 'Supplier', reqd: 0}
		], function(values) {
			frappe.call({
				method: 'erpops.erpops.api.approve_reorder',
				args: {
					item_code: values.item_code,
					qty: values.qty,
					supplier: values.supplier
				},
				callback: function(r) {
					if (r.message && r.message.status === 'created') {
						frappe.show_alert({message: `Draft Purchase Order ${r.message.purchase_order} created successfully.`, indicator: 'green'});
						refresh_alerts();
						refresh_inventory();
						refresh_kpi();
					}
				}
			});
		}, 'Approve Reorder Purchase Order', 'Create Draft PO');
	});

	container.on('click', '.btn-ship-order', function() {
		var so = $(this).attr('data-so');
		frappe.prompt([
			{label: 'Sales Order ID', fieldname: 'so_id', fieldtype: 'Data', default: so, read_only: 1},
			{label: 'Transporter/Carrier', fieldname: 'carrier', fieldtype: 'Data', default: 'FedEx', reqd: 1},
			{label: 'AWB/Tracking Number', fieldname: 'awb', fieldtype: 'Data', placeholder: 'Enter tracking number', reqd: 1}
		], function(values) {
			frappe.call({
				method: 'erpops.erpops.api.mark_dispatched',
				args: {
					sales_order_ids: JSON.stringify([values.so_id]),
					carrier: values.carrier,
					awb_number: values.awb
				},
				callback: function(r) {
					if (r.message) {
						frappe.show_alert({message: `Delivery Note created and order marked dispatched.`, indicator: 'green'});
						refresh_alerts();
						refresh_kpi();
					}
				}
			});
		}, 'Mark Order Dispatched', 'Submit Delivery Note');
	});

	container.on('click', '.btn-snooze-alert', function() {
		var id = $(this).attr('data-id');
		frappe.call({
			method: 'erpops.erpops.api.snooze_alert',
			args: {
				alert_id: id,
				hours: 24
			},
			callback: function(r) {
				frappe.show_alert({message: 'Alert snoozed for 24 hours.', indicator: 'orange'});
				refresh_alerts();
				refresh_kpi();
			}
		});
	});

	// Initial Load
	refresh_kpi();
	refresh_alerts();
	refresh_inventory();
};
