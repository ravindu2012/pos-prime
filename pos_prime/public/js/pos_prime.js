// Open POS Prime workspace shortcut in the desk
$(document).on('click', '.shortcut-widget-box', function (e) {
	var $widget = $(this).closest('.widget');
	var label = $widget.find('.widget-label .ellipsis').text().trim();
	if (label === 'Open POS Prime') {
		e.preventDefault();
		e.stopImmediatePropagation();
		frappe.set_route('pos-terminal');
	}
});
