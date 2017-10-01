ko.bindingHandlers.slider = {
	init: function (element, valueAccessor, allBindingsAccessor) {
		var options = allBindingsAccessor().sliderOptions || {};
		$(element).slider(options);
		ko.utils.registerEventHandler(element, "change", function (event, ui) {
			var observable = valueAccessor();
			observable(ui.value);
		});
		ko.utils.registerEventHandler(element, "slide", function (event, ui) {
			var observable = valueAccessor();
			observable(ui.value);
		});
		ko.utils.domNodeDisposal.addDisposeCallback(element, function () {
			$(element).slider("destroy");
		});
	},
	update: function (element, valueAccessor) {
		var value = ko.utils.unwrapObservable(valueAccessor());
		if (isNaN(value)) value = 0;
		$(element).slider("value", value);
	}
};
