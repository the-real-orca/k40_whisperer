
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


// laser functions
function move(dx, dy) {
	send('move', {dx: parseFloat(dx), dy: parseFloat(dy)})
	return true
}
function moveTo(x, y) {
	send('moveTo', {x: parseFloat(x), y: parseFloat(y)})
	return true
}
function initLaser() {
	send('init')
	return true
}
function releaseLaser() {
	send('release')
	return true
}
function home() {
	send('home')
	return true
}
function stop() {
	send('stop')
	return true
}
function unlock() {
	send('unlock')
	return true
}
function taskRunAll() {
	send('task.run')
	return true
}
function taskRun(id) {
	send('task.run', id)
	return true
}
function taskSaveParams() {
	var params = ko.mapping.toJS(viewModel.selectedTask);
	send('task.set', params)
	return true
}
function workspaceClear() {
	send('workspace.clear')
	return true
}
function workspaceRemoveDrawing(id) {
	send('workspace.remove', id)
	return true
}

// communication
var socket = undefined
function send(cmd, params) {
	if ( !socket || viewModel.instable ) return
	data = {cmd: cmd}
	if ( params !== undefined )
		data.params = params
	data.seqNr = viewModel.seqNr
	console.log("sending ...", data)
	socket.send(data)
}
function handleMessage(data) {
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
		if ( "size" in data.workspace ) {
			viewModel.workspace.width( data.workspace["size"][0] )
			viewModel.workspace.height( data.workspace["size"][1] )
		}
		if ( "originOffset" in data.workspace ) {
			viewModel.workspace.originOffset.x( data.workspace["originOffset"][0] )
			viewModel.workspace.originOffset.y( data.workspace["originOffset"][1] )
		}
		if ( "drawingsOrigin" in data.workspace ) {
			viewModel.workspace.drawingsOrigin.x( data.workspace["drawingsOrigin"][0] )
			viewModel.workspace.drawingsOrigin.y( data.workspace["drawingsOrigin"][1] )
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

	// update tasks
	if ( data.tasks instanceof Array ) {
		viewModel.tasks.removeAll()
		for ( var i = 0; i < data.tasks.length; i++ ) {
			var json = data.tasks[i]
			var task = ko.mapping.fromJS(json);
			viewModel.tasks.push(task)
		}
	}
	
	// update sequence as final step to avoid data races
	// -> intermediate requests will be ignored due-to sequence error
	viewModel.seqNr = data.seqNr
	viewModel.instable = false
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
		drawingsOrigin: {
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
	anchor: ko.observable('upperLeft'),
	tasks: ko.observableArray(),
	selectedTask: ko.observable()
};
// view model functions
viewModel.status.networkIcon = ko.pureComputed(function() {
	return this.status.network() ? "icon-lan-connect" : "icon-lan-disconnect";
}, viewModel);
viewModel.anchor.subscribe(function (val) {
		send('anchor', val)
    }, this)
viewModel.pos.x.subscribe(()=>{moveTo(viewModel.pos.x(), viewModel.pos.y())}, this)
viewModel.pos.y.subscribe(()=>{moveTo(viewModel.pos.x(), viewModel.pos.y())}, this)
viewModel.workspace.drawings.extend({ rateLimit: 100 });
viewModel.tasks.extend({ rateLimit: 100 });

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
	socket.on('message', handleMessage)


}

