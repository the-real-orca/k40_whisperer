
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
function moveWorkspaceOrigin(dx, dy) {
	dx = parseFloat(dx); dy = parseFloat(dy)
	var x = parseFloat(viewModel.workspace.workspaceOrigin.x()) + dx
	var y = parseFloat(viewModel.workspace.workspaceOrigin.y()) + dy
	sendCommand([{cmd: 'move', params: {dx: dx, dy: dy}},
			{cmd: 'workspace.set', params: {workspaceOrigin: [x,y]}}])
	return true
}
function resetWorkspaceOrigin() {
	sendCommand([{cmd: 'home'},
			{cmd: 'workspace.set', params: {workspaceOrigin: [0,0]}}])
	return true
}

function moveTo(x, y) {
	sendCommand('moveTo', {x: parseFloat(x), y: parseFloat(y)})
	return true
}
function initLaser() {
	sendCommand('init')
	return true
}
function releaseLaser() {
	sendCommand('release')
	return true
}
function home() {
	sendCommand('home')
	return true
}
function stop() {
	sendCommand('stop')
	return true
}
function unlock() {
	sendCommand('unlock')
	return true
}

function itemUpdateSelected(item, selected) {		
	if ( !selected.name() )
		selected.name( item.name() )
	else
		selected.name( selected.name() + ", " + item.name() )
	
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

	{
		// compine boundingBoxes
		if ( selected.boundingBox() )
			var selectedBB = selected.boundingBox()
		else
			var selectedBB = [1e12, 1e12, -1e12, -1e12]
		var itemBB = item.boundingBox()
		var xMin = Math.min(selectedBB[0], (itemBB[0] + item.x()))
		var xMax = Math.max(selectedBB[2], (itemBB[2] + item.x()))
		var yMin = Math.min(selectedBB[1], (itemBB[1] + item.y()))
		var yMax = Math.max(selectedBB[3], (itemBB[3] + item.y()))
		selected.boundingBox( [xMin, yMin, xMax, yMax] )
	}
		
	if ( selected.color() === null )
		selected.color( item.color() )
	else if ( selected.color() != item.color() )
		selected.color( undefined )
}
function itemPrepareParams(index=undefined) {
	var selected = viewModel.selectedItem;
	selected.name('')
	selected.x(null)
	selected.y(null)
	selected.dx(0)
	selected.dy(0)
	selected.showAbs(true)
	selected.width(null)
	selected.height(null)
	selected.viewBox(null)
	selected.boundingBox(null)
	selected.color(null)	

	for (var i=0; i < viewModel.workspace.items().length; i++) {
		var item = viewModel.workspace.items()[i]
		if ( index !== undefined )
			item.selected(index==i)
		if ( item.selected() ) {
			itemUpdateSelected(item, selected)
		}
	}

	selected.xset(selected.x())
	selected.yset(selected.y())
	
	return true
}
function itemSaveParams() {
	var selected = viewModel.selectedItem
	var params = ko.mapping.toJS(viewModel.selectedItem)
	if ( params.xset !== undefined ) {
		params.x = params.xset
		params.dx = 0
	}
	if ( params.yset !== undefined ) {
		params.y = params.yset
		params.dy = 0
	}
	cmds = []
	var itemsList = viewModel.workspace.items()
	for (var i=0; i<itemsList.length; i++) {
		var item = itemsList[i]
		if ( item.selected() ) {
			params.id = item.id()
			params.name = item.name()
			cmds.push( prepareCommand('item.set', clone(params)) )
		}
	}
	sendCommand(cmds)
	
	return true
}
function taskRunAll() {
	sendCommand('task.run')
	return true
}
function taskRun(id) {
	sendCommand('task.run', id)
	return true
}
function taskSaveParams() {
	var params = ko.mapping.toJS(viewModel.selectedTask);
	sendCommand('task.set', params)
	return true
}
function workspaceClear() {
	sendCommand('workspace.clear')
	return true
}
function workspaceRemoveItem(id) {
	sendCommand('workspace.remove', id)
	return true
}
function toX(x) {
	x = ko.unwrap(x)
	return viewModel.workspace.homePos.x() + x;
}
function toY(y) {
	y = ko.unwrap(y)
	return viewModel.workspace.height() - (viewModel.workspace.homePos.y() + y);
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
	viewModel.selectedItem.xset(0); viewModel.selectedItem.yset(0)
	viewModel.selectedItem.showAbs(true)
}
function alignAboveOfAxis() {
	var delta = -viewModel.selectedItem.boundingBox()[1]
	viewModel.selectedItem.dy(delta)
	viewModel.selectedItem.showAbs(false)
}
function alignUnderAxis() {
	var delta = -viewModel.selectedItem.boundingBox()[3]
	viewModel.selectedItem.dy(delta)
	viewModel.selectedItem.showAbs(false)
}
function alignLeftOfAxis() {
	var delta = -viewModel.selectedItem.boundingBox()[2]
	viewModel.selectedItem.dx(delta)
	viewModel.selectedItem.showAbs(false)
}
function alignRightOfAxis() {
	var delta = -viewModel.selectedItem.boundingBox()[0]
	viewModel.selectedItem.dx(delta)
	viewModel.selectedItem.showAbs(false)
}


// communication
function prepareCommand(cmd, params) {
	var data = {cmd: cmd}
	if ( params !== undefined )
		data.params = params
	return(data)
}
function sendCommand(cmd, params) {
	if ( viewModel.instable ) return
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
	$.post('/command', JSON.stringify(data), updateStatus)
}
function getStatus() {
	$.ajax({
		type: 'GET',
		url: '/status',
		timeout: 5000,
		success: function(data) {
			viewModel.status.network(true)
			viewModel.alert.network(false)
			updateStatus(data)
		},
		error: function(xhr, type) {
			viewModel.status.network(false)
			viewModel.alert.network(true)
		}
	})
	return true
}
function updateStatus(data) {
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

	// update message
	if ( typeof data.message == "string" ) {
		viewModel.message( data.message )
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
			// get previously selected items
			for ( var i = 0; i < viewModel.workspace.items().length; i++ ) {
				var item = viewModel.workspace.items()[i]
				selectedIDs[item.id()] = item.selected() 
			}
			
			viewModel.workspace.items.removeAll()
			// read itemsList
			for ( var i = 0; i < data.workspace.items.length; i++ ) {
				var json = data.workspace.items[i]
				var item = {
					selected: ko.observable( selectedIDs[json.id] === false ? false : true )	// set previously selected state, auto-select new items
				}
				// set item values
				for ( var key in json )
					item[key] = ko.observable(json[key])
				viewModel.workspace.items.push(item)
			}
		}
	}

	// update tasks
	if ( typeof data.activeTask == "object" ) {
		viewModel.activeTask.id(data.activeTask.id)
		viewModel.activeTask.name(data.activeTask.name)
		viewModel.activeTask.status(data.activeTask.status)
		viewModel.activeTask.progress(data.activeTask.progress)
	}
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
		}),
		fullscreen: ko.observable(isFullscreen())
	},
	alert: {
		laser: ko.observable(false),
		usb: ko.observable(false),
		airassist: ko.observable(false),
		waterTemp: ko.observable(false),
		waterFlow: ko.observable(false),
		network: ko.observable(false)
	},
	message: ko.observable(""),
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
		margin: ko.observable(3),
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
	activeTask: {
		id: ko.observable(""),
		name: ko.observable(""),
		status: ko.observable(""),
		progress: ko.observable(0)
	},
	tasks: ko.observableArray(),
	selectedTask: ko.observable(),
	selectedItem: {
		name: ko.observable(""),
		x: ko.observable(),
		y: ko.observable(),
		xset: ko.observable(),
		yset: ko.observable(),
		dx: ko.observable(0),
		dy: ko.observable(0),
		showAbs: ko.observable(true),
		width: ko.observable(),
		height: ko.observable(),
		viewBox: ko.observable(),
		boundingBox: ko.observable(),
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
viewModel.selectedItem.xset.subscribe((val)=>{ if ( val !== undefined ) viewModel.selectedItem.dx(undefined)}, this)
viewModel.selectedItem.yset.subscribe((val)=>{ if ( val !== undefined ) viewModel.selectedItem.dy(undefined)}, this)
viewModel.selectedItem.dx.subscribe((val)=>{ if ( val !== undefined ) viewModel.selectedItem.xset(undefined)}, this)
viewModel.selectedItem.dy.subscribe((val)=>{ if ( val !== undefined ) viewModel.selectedItem.yset(undefined)}, this)

viewModel.anchor.subscribe(function (val) {
	sendCommand('anchor', val)
}, this)
viewModel.pos.x.subscribe(()=>{moveTo(viewModel.pos.x(), viewModel.pos.y())}, this)
viewModel.pos.y.subscribe(()=>{moveTo(viewModel.pos.x(), viewModel.pos.y())}, this)
viewModel.workspace.items.extend({ rateLimit: 100 })
viewModel.tasks.extend({ rateLimit: 100 })

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
	$("#uploadFile").on("change", ()=>{
		$("#uploadSubmit").click()
	})
	$("#dialog_itemsList").on("change", (event)=>{
		if ( event.target.checked ) {
			var itemsList = viewModel.workspace.items()
			if ( itemsList.length == 1 ) {
				// skip items list, if we have only one item
				itemsList[0].selected(true)
				itemPrepareParams()
				$("#dialog_itemSettings").prop("checked", true)
				$("#dialog_itemsList").prop("checked", false)
			}
		}
	})
	
	// periodic status request
	getStatus()
	setInterval(getStatus, 1000)

	// determine to switch to fullscreen mode
    document.addEventListener('fullscreenchange', fullscreenEventHandler, false);
    document.addEventListener('webkitfullscreenchange', fullscreenEventHandler, false);
    document.addEventListener('mozfullscreenchange', fullscreenEventHandler, false);
    document.addEventListener('MSFullscreenChange', fullscreenEventHandler, false);
	viewModel.touchMode('ontouchstart' in window || navigator.msMaxTouchPoints || window.screen.width <= 1024)
	if ( viewModel.touchMode() )
		viewModel.dialog.fullscreen(true)
}

function isFullscreen() {
    return (document.Fullscreen || document.mozFullScreen || document.webkitIsFullScreen || document.msRequestFullscreen)
}
function fullscreenEventHandler( event ) {
    viewModel.status.fullscreen( isFullscreen() )
}
function enterFullscreen() {
	return enterFullscreenElement(document.documentElement)
}
function enterFullscreenElement(element) {
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
function exitFullscreen() {
	if(document.exitFullscreen) {
		document.exitFullscreen();
	} else if(document.mozCancelFullScreen) {
		document.mozCancelFullScreen();
	} else if(document.webkitExitFullscreen) {
		document.webkitExitFullscreen();
	}
}
