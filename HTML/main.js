
ko.observableArray.fn.pushAll = function(valuesToPush) {
    var underlyingArray = this()
    this.valueWillMutate()
    ko.utils.arrayPushAll(underlyingArray, valuesToPush)
    this.valueHasMutated()
    return this  //optional
};
ko.bindingHandlers.numericValue = {
    init: function(element, valueAccessor) {
		$(element).on("change", ()=>{
			var value = valueAccessor();
			value( parseFloat(element.value) )
		})
    },
	update: function(element, valueAccessor, allBindingsAccessor) {
		var value = parseFloat(ko.utils.unwrapObservable(valueAccessor()))
		var precision = ko.utils.unwrapObservable(allBindingsAccessor().precision) || ko.bindingHandlers.numericValue.defaultPrecision
		element.value = value.toFixed(precision)
	},
	defaultPrecision: 2
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

// laser functions
function move(dx, dy) {
	if ( !socket || viewModel.instable ) return
	socket.send({move: {dx: parseFloat(dx), dy: parseFloat(dy)}, seqNr: viewModel.seqNr})
}
function moveTo(x, y) {
	if ( !socket || viewModel.instable ) return
	socket.send({moveTo: {x: parseFloat(x), y: parseFloat(y)}, seqNr: viewModel.seqNr})
}
function initLaser() {
	if ( !socket ) return
	socket.send({cmd: 'init', seqNr: viewModel.seqNr})
}
function releaseLaser() {
	if ( !socket ) return
	socket.send({cmd: 'release', seqNr: viewModel.seqNr})
}
function home() {
	if ( !socket ) return
	socket.send({cmd: 'home', seqNr: viewModel.seqNr})
}
function stop() {
	if ( !socket ) return
	socket.send({cmd: 'stop', seqNr: viewModel.seqNr})
}
function unlock() {
	if ( !socket || viewModel.instable ) return
	socket.send({cmd: 'unlock', seqNr: viewModel.seqNr})
}
function runTasks() {
	if ( !socket || viewModel.instable ) return
	socket.send({cmd: 'run', params: {task: []}, seqNr: viewModel.seqNr})
}

// view model data
var viewModel = {
	instable: false,
	seqNr: 0,
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
		width: ko.observable(100),
		height: ko.observable(100),
		originOffset: {
			x: ko.observable(0),
			y: ko.observable(0)
		},
		drawings: ko.observableArray()
	},
	pos: {
		valid: ko.observable(false),
		x: ko.observable(0),
		y: ko.observable(0)
	},
	anchor: ko.observable('upperLeft')

};
// view model functions
viewModel.status.networkIcon = ko.pureComputed(function() {
	return this.status.network() ? "icon-lan-connect" : "icon-lan-disconnect";
}, viewModel);
viewModel.anchor.subscribe(function (val) {
		if ( viewModel.instable ) return
		socket.send({anchor: val, seqNr: viewModel.seqNr})
    }, this)
viewModel.pos.x.subscribe(()=>{moveTo(viewModel.pos.x(), viewModel.pos.y())}, this)
viewModel.pos.y.subscribe(()=>{moveTo(viewModel.pos.x(), viewModel.pos.y())}, this)
viewModel.workspace.drawings.extend({ rateLimit: 100 });

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


	// bind view model
	ko.options = {
		deferUpdates: true
	}
	ko.applyBindings(viewModel)
	$("#uploadFile").on("change", (el)=>{
		$("#uploadSubmit").click()
	})

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
		viewModel.instable = true

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
			var x = parseFloat(data.pos.x), y = parseFloat(data.pos.y)
			if ( isNaN(x) || isNaN(y) ) {
				viewModel.pos.valid(false)
			} else {
				viewModel.pos.valid(true)
				viewModel.pos.x(x)
				viewModel.pos.y(y)
			}
		}

		// update anchor
		if ( typeof data.anchor == "string" ) {
			viewModel.anchor( data.anchor )
		}

		// update workspace
		if ( typeof data.workspace == "object" ) {
			if ( "width" in data.workspace )
				viewModel.workspace.width( data.workspace["width"] )
			if ( "height" in data.workspace )
				viewModel.workspace.width( data.workspace["height"] )
			if ( "originOffset" in data.workspace ) {
				viewModel.workspace.originOffset.x( data.workspace["originOffset"][0] )
				viewModel.workspace.originOffset.y( data.workspace["originOffset"][1] )
			}
			if ( data.workspace.drawings instanceof Array ) {
				viewModel.workspace.drawings.removeAll()
				for ( var i = 0; i < data.workspace.drawings.length; i++ ) {
					var json = data.workspace.drawings[i]
					var draw = {}
					for ( var key in json )
						draw[key] = ko.observable(json[key])
					viewModel.workspace.drawings.push(draw)
				}
			}
		}

		// update sequence as final step to avoid data races
		// -> intermediate requests will be ignored due-to sequence error
		viewModel.seqNr = data.seqNr
		viewModel.instable = false
	})



}

