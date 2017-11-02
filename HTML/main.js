
ko.observableArray.fn.pushAll = function(valuesToPush) {
    var underlyingArray = this()
    this.valueWillMutate()
    ko.utils.arrayPushAll(underlyingArray, valuesToPush)
    this.valueHasMutated()
    return this  //optional
};
function fxFadeIn(elem) {
	if (elem.nodeType === 1) {
		$(elem).addClass("fadeIn").on('animationend webkitAnimationEnd', function(){ $(elem).removeClass("fadeIn")})
	}
}
function fxSlideUpRemove(elem) {
	if (elem.nodeType === 1) {
		$(elem).addClass("slideUp").on('animationend webkitAnimationEnd', function(){ $(elem).remove(); })
	}
}


var socket = undefined
// view model data
var viewModel = {
	status: {
		laser: ko.observable(0),
		usb: ko.observable(false),
		airassist: ko.observable(0),
		waterTemp: ko.observable(0),
		waterFlow: ko.observable(0),
		network: ko.observable(false)
	},
	alert: {
		laser: ko.observable(false),
		usb: ko.observable(false),
		airassist: ko.observable(false),
		waterTemp: ko.observable(false),
		waterFlow: ko.observable(false),
		network: ko.observable(false)
	},
	config: {
		stepSize: ko.observable(2)
	},
	workspace: {
		width: ko.observable(0),
		height: ko.observable(0)
	},
	pos: {
		x: ko.observable(0),
		y: ko.observable(0)
	},
	anchor: ko.observable('upperLeft')

};
// view model functions
viewModel.move = function(dx, dy) {
		socket.emit("json", {move: {
			dx: dx,
			dy: dy
		}})
	}
viewModel.anchor.subscribe(function (val) {
		socket.emit("json", {anchor: val})
    }, this)



function init() {

	// add pressed / released events for buttons
	var eventPressed = null
	$('button, .button').on('touchstart', function(e) { 
		if ( eventPressed ) {
			if ( eventPressed.target == e.target )		// ignore multiple events on same target
				return;									
			$(eventPressed.target).trigger('released');	// release previous element
		}
		eventPressed = e
		$(e.target).trigger('pressed', e)
	})
	$(document).on('touchend', function(ex) {
		if ( !eventPressed )
			return;
		$(eventPressed.target).trigger('released', ex)
		eventPressed = null;
	})	
	$('button, .button').on('mousedown', function(e) { 
		if ( eventPressed ) {
			if ( eventPressed.target == e.target )		// ignore multiple events on same target
				return;						
			$(eventPressed.target).trigger('released');	// release previous element
		}
		eventPressed = e
		if ( e.button == 0 ) {$(e.target).trigger('pressed', e)} // react on left mouse button
	})
	$(document).on('mouseup', function(ex) {
		if ( !eventPressed )
			return
		$(eventPressed.target).trigger('released', ex)
		eventPressed = null
	})
	$('button, .button').on('keypress', function(e) { if ( e.key == ' ' || e.keyCode == 32 ) {$(e.target).trigger('pressed', e);} })
	$('button, .button').on('keyup', function(e) { if ( e.key == ' ' || e.keyCode == 32 ) {$(e.target).trigger('released', e);} })		
	
	
	// init messages
	init_msg()
	
	
	// bind model
	ko.applyBindings(viewModel)

	// init Web Sockets
	socket = io.connect()
		
	// socket connected to server
	socket.on('connect', function() {
		viewModel.status.network(true);
		viewModel.alert.network(false);
	})
    // socket disconnected to server
	socket.on('disconnect', function() {
		viewModel.status.network(false);
		viewModel.alert.network(true);
	})
	// handle socket error
	socket.on('error', function(err) {
		console.error('Socket Error:', err)
		// TODO add notification
	})

	// handle incomming message
	socket.on('message', function(data) {
		console.log('Received message', data)
		
		// update status
		if ( typeof data.status == "object" ) {
			for ( var key in data.status )
				viewModel.status[key]( data.status[key] )
		}
		if ( typeof data.alert == "object" ) {
			for ( var key in data.alert )
				viewModel.alert[key]( data.alert[key] )
		}
	
		// update position
		if ( typeof data.pos == "object" ) {
			viewModel.pos.x( data.pos.x )
			viewModel.pos.y( data.pos.y )
		}

		// update anchor
		if ( typeof data.anchor == "string" ) {
			viewModel.anchor( data.anchor )
		}

		
		// TODO
	})

	
}

