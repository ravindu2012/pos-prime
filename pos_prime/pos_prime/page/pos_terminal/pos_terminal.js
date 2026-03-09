frappe.pages['pos-terminal'].on_page_load = function(wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __('POS Prime'),
		single_column: true,
	});

	// v16: keep the small page-head navbar (like /point-of-sale)
	// v14/v15: remove it entirely for full-screen layout
	var isV16 = !!document.querySelector('.body-sidebar-container');
	if (!isV16) {
		$(wrapper).find('.page-head').remove();
	}

	// Match navbar width: remove .container max-width, use navbar's 1rem padding
	var fullWidth = 'max-width:100%!important;width:100%!important;margin:0!important;padding-left:1rem!important;padding-right:1rem!important;';
	var noPad = 'padding:0!important;margin:0!important;max-width:100%!important;width:100%!important;';
	$(wrapper).find('.page-body').each(function() { this.style.cssText += fullWidth; });
	$(wrapper).find('.page-wrapper').each(function() { this.style.cssText += noPad; });
	$(wrapper).find('.layout-main').each(function() { this.style.cssText += noPad; });
	$(wrapper).find('.layout-main-section-wrapper').each(function() { this.style.cssText += noPad; });
	$(wrapper).find('.layout-main-section').each(function() { this.style.cssText += noPad; });

	// Create mount point
	$(wrapper).find('.layout-main-section').html('<div id="pos-prime-app"></div>');

	// Hide Frappe desk sidebar permanently on this page
	// v14/v15: aside.desk-sidebar   v16: .body-sidebar-container
	$('aside.desk-sidebar, .desk-sidebar, .body-sidebar-container').hide();

	// Size it to fill remaining viewport
	setTimeout(sizePosApp, 0);
	window.addEventListener('resize', sizePosApp);
	// Adapt when Frappe desk sidebar is toggled
	$(document.body).on('toggleSidebar', function() {
		setTimeout(sizePosApp, 300);
	});

	window.csrf_token = frappe.csrf_token;
	load_pos_prime_assets();
};

frappe.pages['pos-terminal'].on_page_show = function() {
	// Re-hide sidebar when returning to this page
	$('aside.desk-sidebar, .desk-sidebar, .body-sidebar-container').hide();
	sizePosApp();
	window.addEventListener('resize', sizePosApp);
};

frappe.pages['pos-terminal'].on_page_hide = function() {
	window.removeEventListener('resize', sizePosApp);
	// Restore sidebar when navigating away
	$('aside.desk-sidebar, .desk-sidebar, .body-sidebar-container').show();
};

function sizePosApp() {
	var el = document.getElementById('pos-prime-app');
	if (!el) return;
	var top = el.getBoundingClientRect().top;
	el.style.height = 'calc(100vh - ' + Math.round(top) + 'px)';
	el.style.overflow = 'hidden';
}

async function load_pos_prime_assets() {
	try {
		var manifestRes = await fetch('/assets/pos_prime/frontend/.vite/manifest.json');
		if (!manifestRes.ok) {
			throw new Error('Manifest not found (HTTP ' + manifestRes.status + ')');
		}
		var manifest = await manifestRes.json();

		var entry = manifest['index.html'] || manifest['src/main.ts'];
		if (!entry) {
			throw new Error('Entry point not found in manifest');
		}

		var cssFiles = new Set();
		function collectCSS(chunk) {
			if (chunk.css) {
				chunk.css.forEach(function(f) { cssFiles.add(f); });
			}
			if (chunk.imports) {
				chunk.imports.forEach(function(key) {
					if (manifest[key]) collectCSS(manifest[key]);
				});
			}
		}
		collectCSS(entry);

		cssFiles.forEach(function(cssFile) {
			if (!document.querySelector('link[href$="' + cssFile + '"]')) {
				var link = document.createElement('link');
				link.rel = 'stylesheet';
				link.href = '/assets/pos_prime/frontend/' + cssFile;
				document.head.appendChild(link);
			}
		});

		await import('/assets/pos_prime/frontend/' + entry.file);

		// Re-size after Vue app mounts
		setTimeout(sizePosApp, 100);
	} catch (e) {
		console.error('Failed to load POS Prime:', e);
		var el = document.getElementById('pos-prime-app');
		if (el) {
			el.innerHTML =
				'<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#666;">' +
				'<div style="text-align:center;">' +
				'<p style="font-size:16px;font-weight:600;">Failed to load POS Prime</p>' +
				'<p style="font-size:13px;margin-top:8px;color:#999;">' + e.message + '</p>' +
				'<p style="font-size:13px;margin-top:8px;"><a href="#" onclick="location.reload();return false;" style="color:#2490ef;">Try refreshing</a></p>' +
				'</div></div>';
		}
	}
}
