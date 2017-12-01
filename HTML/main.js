
function clone(obj) {
	return JSON.parse(JSON.stringify(obj));
}

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
		try {
			element.value = value.toFixed(precision)
		} catch (e) {
			element.value = false;
		}
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
function getStatus() {
	send('status')
	return true
}
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

function itemUpdateSelected(item, selected) {		
	selected.names.push( item.name() )
	
	if ( selected.x() === null )
		selected.x( item.x() )
	else if ( selected.x() != item.x() )
		selected.x( undefined )
	
	if ( selected.y() === null )
		selected.y( item.y() )
	else if ( selected.y() != item.y() )
		selected.y( undefined )
	
	if ( selected.width() === null )
		selected.width( item.width() )
	else if ( selected.width() != item.width() )
		selected.width( undefined )
		
	if ( selected.height() === null )
		selected.height( item.height() )
	else if ( selected.height() != item.height() )
		selected.height( undefined )
		
	if ( selected.viewBox() === null )
		selected.viewBox( item.viewBox() )
	else if ( selected.viewBox() != item.viewBox() )
		selected.viewBox( undefined )
		
	if ( selected.color() === null )
		selected.color( item.color() )
	else if ( selected.color() != item.color() )
		selected.color( undefined )
}
function itemOpenParams(index=undefined) {
	var selected = viewModel.selectedItem;
	selected.names.removeAll()
	selected.x(null)
	selected.y(null)
	selected.width(null)
	selected.height(null)
	selected.viewBox(null)
	selected.color(null)	

	for (var i=0; i < viewModel.workspace.items().length; i++) {
		var item = viewModel.workspace.items()[i]
		if ( index !== undefined )
			item.selected(index==i)
		if ( item.selected() ) {
			itemUpdateSelected(item, selected)
		}
	}
	
	return true
}
function itemSaveParams() {
	var selected = viewModel.selectedItem
	var params = ko.mapping.toJS(viewModel.selectedItem)
	params.names = undefined
	cmds = []
	for (var i in viewModel.workspace.items()) {
		var item = viewModel.workspace.items()[i]
		if ( item.selected() ) {
			params.id = item.id()
			params.name = item.name()
			cmds.push( prepareCommand('item.set', clone(params)) )
		}
	}
	send(cmds)
	
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
function workspaceRemoveItem(id) {
	send('workspace.remove', id)
	return true
}
function toX(x) {
	x = ko.unwrap(x)
	return x;
}
function toY(y) {
	y = ko.unwrap(y)
	return viewModel.workspace.height() - y;
}
function workX(x) {
	x = ko.unwrap(x)
	return toX(viewModel.workspace.workspaceOrigin.x() + x);
}
function workY(y) {
	y = ko.unwrap(y)
	return toY(viewModel.workspace.workspaceOrigin.y() + y);
}

function alignToOrigin() {
	var item = viewModel.selectedItem()
	item.x(0); item.y(0)
}

function alignAboveOfAxis() {
	item.y(-item.viewBox()[3])
}

function alignUnderOfAxis() {
	item.y(0)
}

function alignLeftOfAxis() {
	item.x(-item.viewBox()[2])
}

function alignRightOfAxis() {
	item.x(0)
}

function alignToTop() {
	var item = viewModel.selectedItem()
	var delta = item.viewBox()[3] + item.viewBox()[1]
	var box = viewModel.workspace.viewBox()
	item.y(box[3] + box[1] - delta)
}

function alignToLeft() {
	var item = viewModel.selectedItem()
	var box = viewModel.workspace.viewBox()
	item.x(box[0] - item.viewBox()[0])
}

function alignToBottom() {
	var item = viewModel.selectedItem()
	var box = viewModel.workspace.viewBox()
	item.y(box[1] - item.viewBox()[1])
}

function alignToRight() {
	var item = viewModel.selectedItem()
	var delta = item.viewBox()[2] + item.viewBox()[0]
	var box = viewModel.workspace.viewBox()
	item.x(box[2] + box[0] - delta)
}



// communication
var socket = undefined
function prepareCommand(cmd, params) {
	var data = {cmd: cmd}
	if ( params !== undefined )
		data.params = params
	return(data)
}
function send(cmd, params) {
	if ( !socket || viewModel.instable ) return
	var data
	if ( cmd instanceof Array ) {
		data = {
			multiple: cmd
		}
	} else {
		data = prepareCommand(cmd, params)
	}	
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
		if ( "width" in data.workspace )
			viewModel.workspace.width( data.workspace["width"] )
		if ( "height" in data.workspace )
			viewModel.workspace.height( data.workspace["height"] )
		if ( "homePos" in data.workspace ) {
			viewModel.workspace.homePos.x( data.workspace["homePos"][0] )
			viewModel.workspace.homePos.y( data.workspace["homePos"][1] )
		}
		if ( "workspaceOrigin" in data.workspace ) {
			viewModel.workspace.workspaceOrigin.x( data.workspace["workspaceOrigin"][0] )
			viewModel.workspace.workspaceOrigin.y( data.workspace["workspaceOrigin"][1] )
		}
		if ( "viewBox" in data.workspace )
			viewModel.workspace.viewBox( data.workspace["viewBox"] )
		
		if ( data.workspace.items instanceof Array ) {
			var selectedIDs = {}
			for ( var i = 0; i < viewModel.workspace.items().length; i++ ) {
				var item = viewModel.workspace.items()[i]
				selectedIDs[item.id()] = item.selected() 
			}
			selectedCount=0
			viewModel.workspace.items.removeAll()
			for ( var i = 0; i < data.workspace.items.length; i++ ) {
				var json = data.workspace.items[i]
				var item = {
					selected:ko.observable( selectedIDs[json.id] )
				}
				if ( item.selected() )
					selectedCount++
				for ( var key in json )
					item[key] = ko.observable(json[key])
				viewModel.workspace.items.push(item)
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
function uploadFile() {
	$("#uploadFile").first().val("").click()
}
function sendFile() {
	var file = $("#uploadFile")[0].files[0]
	
	// check that file ia an image
	if (!file)
		return;

	// indicate uploading
	viewModel.wait("<i class='icon-upload x-large'></i><br>" + file.name);

	// build form data object
	var fd = new FormData();
	fd.append('file', file); // append the file
    $.ajax({
        url: '/upload',
        type: 'POST',
        success: function() {
			console.log("upload ok")
			viewModel.continue()
			getStatus()
        },
        error: function() {
			viewModel.continue()
			console.error("cannot uploade: " + file.name)
			add_msg('error', "upload error", "cannot uploade: " + file.name)
			getStatus()
        },
        data: fd,
        contentType: false,
        processData: false,
        cache: false
    });
}


// view model data
var viewModel = {
	instable: false,
	touchMode: ko.observable(false),
	seqNr: 0,
	status: {
		laser: ko.observable(0),
		usb: ko.observable(false),
		airassist: ko.observable(0),
		waterTemp: ko.observable(0),
		waterFlow: ko.observable(0),
		network: ko.observable(false),
		networkIcon: ko.pureComputed(function() {
			return viewModel.status.network() ? "icon-lan-connect" : "icon-lan-disconnect";
		})		
	},
	alert: {
		laser: ko.observable(false),
		usb: ko.observable(false),
		airassist: ko.observable(false),
		waterTemp: ko.observable(false),
		waterFlow: ko.observable(false),
		network: ko.observable(false)
	},
	unit: {
		pos: ko.observable("mm"),
		speed: ko.observable("mm/s"),
		temp: ko.observable("°C"),
		flow: ko.observable("l/min")
	},
	config: {
		stepSize: ko.observable(2)
	},
	workspace: {
		width: ko.observable(100),
		height: ko.observable(100),
		homePos: {
			x: ko.observable(0),
			y: ko.observable(0)
		},
		workspaceOrigin: {
			x: ko.observable(0),
			y: ko.observable(0)
		},
		viewBox: ko.observable([0,0,0,0]),
		items: ko.observableArray()
	},
	pos: {
		valid: ko.observable(false),
		x: ko.observable(0),
		y: ko.observable(0)
	},
	anchor: ko.observable('upperLeft'),
	tasks: ko.observableArray(),
	selectedTask: ko.observable(),
	selectedItem: {
		names: ko.observableArray(),
		x: ko.observable(),
		y: ko.observable(),
		width: ko.observable(),
		height: ko.observable(),
		viewBox: ko.observable(),
		color: ko.observable()		
	},
	selectedItemsAll: ko.pureComputed({
		read: function() {
			selectedCount=0
			for ( var i = 0; i < viewModel.workspace.items().length; i++ ) {
				var item = viewModel.workspace.items()[i]
				if ( item.selected() )
					selectedCount++
			}
			return ( selectedCount == viewModel.workspace.items().length )
		},
		write: function(val) {
			for ( var i = 0; i < viewModel.workspace.items().length; i++ ) {
				var item = viewModel.workspace.items()[i]
				item.selected(val)
			}			
		},
		owner: this
	}),
	dialog: {
		fullscreen: ko.observable(false)
	},
	wait: ko.observable(false)
	
};
// view model functions
viewModel.continue = function() {
	viewModel.wait(false)
}
viewModel.anchor.subscribe(function (val) {
	send('anchor', val)
}, this)
viewModel.pos.x.subscribe(()=>{moveTo(viewModel.pos.x(), viewModel.pos.y())}, this)
viewModel.pos.y.subscribe(()=>{moveTo(viewModel.pos.x(), viewModel.pos.y())}, this)
viewModel.workspace.items.extend({ rateLimit: 100 });
viewModel.tasks.extend({ rateLimit: 100 });

function init() {
	
/*	
	$(".title").on('click', function() {
		enterFullscreen()
	})
*/
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
	$("#uploadFile").on("change", ()=>{
		$("#uploadSubmit").click()
	})
	$("#dialog_itemsList").on("change", (event)=>{
		if ( event.target.checked ) {
			if ( viewModel.workspace.items().length == 1 ) {
				// skip items list, if we have only one item
				// TODO viewModel.selectedItem( viewModel.workspace.items()[0] )
				$("#dialog_itemSettings").prop("checked", true);
				$("#dialog_itemsList").prop("checked", false);
			}
		}
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


	// determine to switch to fullscreen mode
	viewModel.touchMode('ontouchstart' in window || navigator.msMaxTouchPoints || window.screen.width <= 1024)
	if ( viewModel.touchMode() )
		viewModel.dialog.fullscreen(true)
}

function fullscreen() {
	return fullscreenElement(document.documentElement)
}
function fullscreenElement(element) {
	if(element.requestFullscreen) {
		element.requestFullscreen()
	} else if(element.mozRequestFullScreen) {
		element.mozRequestFullScreen()
	} else if(element.msRequestFullscreen) {
		element.msRequestFullscreen()
	} else if(element.webkitRequestFullscreen) {
		element.webkitRequestFullscreen()
	}
	return true
}
