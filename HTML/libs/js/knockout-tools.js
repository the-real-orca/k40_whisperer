ko.observableTracked = function( initialValue, timeout ) {

	//private variables
	var _value = ko.observable(initialValue);
	var _modificationTime = 0;
	
	//computed observable that we will return
	var result = ko.computed({
		read: function() {
			return _value();
		},
		write: function(val) {
			if ( val != _value() ) {
				_modificationTime = new Date().getTime();
				_value( val );
			}
		}
	});
	
	if ( timeout === undefined )
		timeout = 1000;
	if ( ko.isObservable( timeout ) )
		result.timeout = timeout;
	else
		result.timeout = ko.observable(timeout);

	result.modificationTime = function() {
		return _modificationTime;
	};

	result.setIfUnchanged = function(val) {
		var waitTill = _modificationTime + parseInt(this.timeout());
		if ( ( val != _value() ) && 
			( waitTill < new Date().getTime() ) ) {
			_value( val );
			return true;
		}
		return false;
	};
	
	
	return result;
}

ko.callOnInterval = function( callback, defaultInterval ) {
	//private variables
	var _defaultInterval = defaultInterval || 500;
	var _value = ko.observable(false);
	var _handle = false;
	
	//computed observable that we will return
	var result = ko.computed({
		read: function() {
			var val = _value();
			return val;
		},
		write: function(val) {
			if ( val === true ) {
				val = _value() || _defaultInterval;
			}

			if ( val == _value() ) {
				// do nothing
				return;
			}

			if ( val > 0 ) {
				// set interval
				_value( val );
				_defaultInterval = val;

		
				if (_handle ) {
					clearInterval( _handle );
				} else {
					// directly execute callback
					callback();
				}

				_handle = setInterval(callback, val);
			}
			else {
				if ( _handle ) {
					clearInterval( _handle );
					_handle = false; 
				}
				_value( false );
			}
		}
	});
	
	return result;
}

function initPosSliderSend(viewModel) {
	viewModel._slider_send = ko.computed({
		read: function() {
			var val = this.pos_set();
			if ( this.autoUpdate() && this.dataValid() ) {
				sendPos( this, val );
			}
			return val;
		}
	}, viewModel).extend({ throttle: 100 });
}

function initViewModel(viewModel, moduleName, moduleAddr ) {
	viewModel.baseURL = ko.observable("../."); 
	viewModel.modul_name = ko.observable(moduleName);
	viewModel.modul_addr = ko.observable(moduleAddr);
	viewModel.error = ko.observable(false);					///< client error
	viewModel.info = ko.observable(false);					///< client info message
	viewModel.networkError = ko.observable(false);			///< network error
	viewModel.networkActive = ko.observable(false);			///< network traffic
	viewModel.dataValid = ko.observable(false);				///< data received
	viewModel.autoUpdate = ko.callOnInterval( update, 200);		///< continuously update data

	
	// init command buttons
	initCommands( viewModel );
	
	// send details
	var old_data = [];
	viewModel.send = function() {
		var data = modelToData(viewModel, viewModel._datamap());
		if ( JSON.stringify(data) != JSON.stringify(old_data) )
			sendData(viewModel, viewModel.modul_addr(), data );
		old_data = data;
	};
	
	// network control buttons
	viewModel.networkUpdate = function() {
		viewModel.autoUpdate(true);
		viewModel.networkError(false);
		viewModel.networkActive(false);
		viewModel.error(false);
		viewModel.info(false);
	};
	viewModel.networkPause = function() {
		viewModel.autoUpdate(false);
		viewModel.networkError(false);
		viewModel.networkActive(false);
		viewModel.error(false);
		viewModel.info(false);
	};
	
}

