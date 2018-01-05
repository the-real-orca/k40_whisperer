
function clone(obj) {
	return JSON.parse(JSON.stringify(obj))
}
function uuid() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8)
    return v.toString(16)
  })
}

ko.observableArray.fn.pushAll = function(valuesToPush) {
	var underlyingArray = this()
	this.valueWillMutate()
	ko.utils.arrayPushAll(underlyingArray, valuesToPush)
	this.valueHasMutated()
	return this  //optional
};
ko.observable.fn.update = function(value) {
	if ( this() == value )
		return
	if ( typeof(this.suppressUpdate) == "function" ) {
		if ( this.suppressUpdate() )
			return
	} else {
		if ( this.suppressUpdate )
			return
	}
	this(value)
	return this  //optional
};
ko.extenders.suppressUpdate = function(target, option) {
    target.suppressUpdate = option
    return target
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
/* TODO
ko.extenders.logChange = function(target, option) {
    target.subscribe(function(newValue) {
       console.log(option + ": " + newValue)
    });
    return target
}
ko.extenders.confirmable = function(target, options) {
    var message = options.message;
    var unless = options.unless || function() { return false; }
    //create a writeable computed observable to intercept writes to our observable
    var result = ko.computed({
        read: target,  //always return the original observables value
        write: function(newValue) {
            var current = target()

            //ask for confirmation unless you don't have
            if (unless() || confirm(message)) {
                target(newValue)
            } else {
              target.notifySubscribers(current)
            }
        }
    }).extend({ notify: 'always' })

    //return the new computed observable
    return result
}
var viewModel = {
	myvalue: ko.observable(false).extend({confirmable: "Are you sure?"});
    myvalue: ko.observable(false).extend({confirmable: { message: "Are you sure?", unless: function() { return new Date().getMonth() == 2 }} });
}
*/
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
	var x = parseFloat(viewModel.workspace.workspaceOrigin.x()) + parseFloat(dx)
	var y = parseFloat(viewModel.workspace.workspaceOrigin.y()) + parseFloat(dy)
	sendCommand('workspace.origin', [x,y])
	return true
}
function resetWorkspaceOrigin() {
	sendCommand([{cmd: 'home'},
			{cmd: 'workspace.set', params: {indicator: 'origin', workspaceOrigin: [0,0]}}])
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
	sendCommand('profile.run')
	return true
}
function taskRun(id) {
	sendCommand('profile.run', id)
	return true
}
function taskSave() {
	var params = {
		id: viewModel.profile.id(),
		name: viewModel.profile.name(),
		tasks: ko.mapping.toJS(viewModel.tasks)
	}
	sendCommand('profile.set', params)
	return true
}
function taskStatusIcon(status) {
	switch (status) {
		case 'wait':
			return "icon-hourglass"
		case 'prepare':
			return "icon-cog animate-spin"
		case 'running':
			return "icon-flash"
		case 'finished':
			return "icon-ok"
		case 'error':
			return "icon-cancel"
		case 'stopped':
			return "icon-stop"
		case 'empty':
			return "icon-minus"
		default:
			return "" // icon-ellipsis-horizontal
	}
}
function taskStatusColor(status) {
	switch (status) {
		case 'prepare':
		case 'running':
		case 'stopped':
			return "#0074d980"
		case 'finished':
			return "#2ecc4080"
		case 'error':
			return "#ff413680"
		case 'wait':
		case 'empty':
		default:
			return "#cccccc"
	}
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
	viewModel.suppressUntil = Date.now() + 1000 // suppress updates for 1 Second
	console.log("sending ...", data)
// TODO	$.post('/command', JSON.stringify(data), updateStatus)
	$.ajax({
		type: 'POST',
		url: '/command',
		data: JSON.stringify(data),
		dataType: 'application/json',
		timeout: 1000,
		success: function(data) {},
		error: function(xhr, type) {
			viewModel.suppressUntil = 0
		}
	})
	return true

}
function taskViewModel(data={}, task) {
	if ( !data.id )
		data.id = uuid()
	if ( typeof task == "object" ) {
		task.id.update(data.id)
		if ( data.name !== undefined )
			task.name.update(data.name)
		if ( data.colors !== undefined )
			task.colors.update(data.colors)
		if ( data.speed !== undefined )
			task.speed.update( parseFloat(data.speed) )
		if ( data.intensity !== undefined )
			task.intensity.update( parseFloat(data.intensity) )
		if ( data.type !== undefined )
			task.type.update(data.type)
		if ( data.repeat !== undefined )
			task.repeat.update( parseInt(data.repeat) )
		if ( data.status !== undefined )
			task.status.update(data.status)
		if ( data.progress !== undefined )
			task.progress.update( parseFloat(data.progress) )
	} else {
		task = {
			id: viewable(data.id),
			name: editable(data.name),
			colors: editable(data.colors),
			speed: editable(data.speed),
			intensity: editable(data.intensity),
			type: editable(data.type),
			repeat: editable(data.repeat),
			status: viewable(data.status),
			progress: viewable(data.progress)
		}
		task.statusIcon = ko.pureComputed(function() { return taskStatusIcon(this.status()) }, task)
		task.statusColor = ko.pureComputed(function() { return taskStatusColor(this.status()) }, task)
	}
	return task
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
function suppressUpdate() { return viewModel.editMode() }
function updateStatus(data) {
	viewModel.instable = true

	// update status
	if ( typeof data.status == "object" ) {
		for ( var key in data.status )
			viewModel.status[key].update( data.status[key] )
	}
	if ( typeof data.alert == "object" ) {
		for ( var key in data.alert )
			viewModel.alert[key].update( data.alert[key] )
	}

	// update position
	if ( typeof data.pos == "object" ) {
		var x = parseFloat(data.pos.x), y = parseFloat(data.pos.y)
		if ( isNaN(x) || isNaN(y) ) {
			viewModel.pos.valid.update(false)
		} else {
			viewModel.pos.valid.update(true)
			viewModel.pos.x.update(x)
			viewModel.pos.y.update(y)
		}
	}

/* TODO
	// update message
	if ( typeof data.message == "string" ) {
		viewModel.message.update( data.message )
	}
*/

	// update workspace
	if ( typeof data.workspace == "object" ) {
		if ( "width" in data.workspace )
			viewModel.workspace.width.update( data.workspace["width"] )
		if ( "height" in data.workspace )
			viewModel.workspace.height.update( data.workspace["height"] )
		if ( "homePos" in data.workspace ) {
			viewModel.workspace.homePos.x.update( data.workspace["homePos"][0] )
			viewModel.workspace.homePos.y.update( data.workspace["homePos"][1] )
		}
		if ( "workspaceOrigin" in data.workspace ) {
			viewModel.workspace.workspaceOrigin.x.update( data.workspace["workspaceOrigin"][0] )
			viewModel.workspace.workspaceOrigin.y.update( data.workspace["workspaceOrigin"][1] )
		}
		if ( "indicator" in data.workspace)
			viewModel.workspace.indicator.update( data.workspace["indicator"] )

		if ( "viewBox" in data.workspace )
			viewModel.workspace.viewBox.update( data.workspace["viewBox"] )

		if ( data.workspace.items instanceof Array ) {
			var selectedIDs = {}
			// get previously selected items
			for ( var i = 0; i < viewModel.workspace.items().length; i++ ) {
				var item = viewModel.workspace.items()[i]
				selectedIDs[item.id()] = item.selected()
			}

			// TODO -> update items list instead of overwriting !!!
			viewModel.workspace.items.removeAll()
			// read itemsList
			for ( var i = 0; i < data.workspace.items.length; i++ ) {
				var json = data.workspace.items[i]
				var item = {
					selected: viewable( selectedIDs[json.id] === false ? false : true )	// set previously selected state, auto-select new items
				}
				// set item values
				for ( var key in json )
					item[key] = editable(json[key])
				viewModel.workspace.items.push(item)
			}
		}
	}

	// update profiles / tasks
	if ( typeof data.profile == "object" ) {
		if ( data.profile.profiles instanceof Array ) {
			var profiles = viewModel.profile.list()
			// prepare task list
			for ( var i = 0; i < profiles.length; i++ )
				profiles[i].remove = true

			// update with received profiles
			for ( var i = 0; i < data.profile.profiles.length; i++ ) {
				var json = data.profile.profiles[i]
				for ( var i = 0; i < profiles.length; i++ )
					if ( profiles[i].id == json.id ) {
						// task found -> update
						profiles[i].name = json.name
						profiles[i].remove = false
						break
					}
				if ( i == profiles.length ) {
					// new profile -> append
					viewModel.profile.list.push({ id: json.id, name: json.name })
				}
			}

			// clean-up
			viewModel.profile.list.remove((item)=>{ return item.remove })
		}

		if ( "active" in data.profile ) {
			var profile = data.profile.active

			// active profile
			viewModel.profile.id( profile["id"] )
			if ( "name" in profile )
				viewModel.profile.name.update( profile["name"] )

			// tasks
			if ( profile.tasks instanceof Array ) {
				var tasks = viewModel.tasks()
				// prepare task list
				for ( var i = 0; i < tasks.length; i++ )
					tasks[i].remove = true

				// update with received tasks
				for ( var i = 0; i < profile.tasks.length; i++ ) {
					var json = profile.tasks[i]
					for ( var i = 0; i < tasks.length; i++ )
						if (tasks[i].id() == json.id) {
							// task found -> update
							var task = tasks[i]
							taskViewModel(json, task)
							task.remove = false
							break
						}
					if ( i == tasks.length ) {
						// new task -> append
						var task = taskViewModel(json);
						viewModel.tasks.push(task)
					}
				}

				// clean-up
				viewModel.tasks.remove((item)=>{ return item.remove })
			}
		}
	}

	// update sequence as final step to avoid data races
	// -> intermediate requests will be ignored due-to sequence error
	if ( !suppressUpdate() )
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
	viewModel.dialog.wait("<i class='icon-upload x-large'></i><br>" + file.name);

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
function viewable(val) { return ko.observable(val) }
function editable(val) { return ko.observable(val).extend({suppressUpdate: suppressUpdate}) }
var viewModel = {
	instable: false,
	editMode: ko.pureComputed(function() { return (viewModel.dialog.itemsSettings() || viewModel.dialog.taskSettings() || viewModel.suppressTimer()) ? true : false }),
	suppressTimer: viewable(false),
	touchMode: viewable(false),
	seqNr: 0,
	status: {
		laser: viewable(0),
		usb: viewable(false),
		airassist: viewable(0),
		waterTemp: viewable(0),
		waterFlow: viewable(0),
		network: viewable(false),
		networkIcon: ko.pureComputed(function() { return viewModel.status.network() ? "icon-lan-connect" : "icon-lan-disconnect"; }),
		fullscreen: viewable(isFullscreen())
	},
	alert: {
		laser: viewable(false),
		usb: viewable(false),
		airassist: viewable(false),
		waterTemp: viewable(false),
		waterFlow: viewable(false),
		network: viewable(false)
	},
	unit: {
		pos: editable("mm"),
		speed: editable("mm/s"),
		temp: editable("°C"),
		flow: editable("l/min")
	},
	config: {
		stepSize: editable(2)
	},
	workspace: {
		margin: viewable(3),
		width: editable(100),
		height: editable(100),
		homePos: {
			x: editable(0),
			y: editable(0),
		},
		workspaceOrigin: {
			x: editable(0),
			y: editable(0)
		},
		viewBox: viewable([0,0,0,0]),
		indicator: viewable(""),
		items: ko.observableArray()
	},
	pos: {
		valid: viewable(false),
		x: viewable(0),
		y: viewable(0)
	},
	profile: {
		id: viewable(),
		name: editable(),
		selected: viewable(),
		list: ko.observableArray()
	},
	tasks: ko.observableArray(),
	selectedTask: ko.observable(),
	selectedItem: {
		name: editable(""),
		x: editable(),
		y: editable(),
		xset: editable(),
		yset: editable(),
		dx: editable(0),
		dy: editable(0),
		showAbs: editable(true),
		width: editable(),
		height: editable(),
		viewBox: editable(),
		boundingBox: editable(),
		color: editable()
	},
	selectAllItems: ko.pureComputed({
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
		fullscreen: viewable(false),
		itemsList: viewable(false),
		itemsSettings: viewable(false),
		taskSettings: viewable(false),
		wait: viewable(false)
	}
};
// view model functions
viewModel.continue = function() { viewModel.dialog.wait(false) }
viewModel.selectedItem.xset.subscribe((val)=>{ if ( val !== undefined ) viewModel.selectedItem.dx(undefined) }, this)
viewModel.selectedItem.yset.subscribe((val)=>{ if ( val !== undefined ) viewModel.selectedItem.dy(undefined) }, this)
viewModel.selectedItem.dx.subscribe((val)=>{ if ( val !== undefined ) viewModel.selectedItem.xset(undefined) }, this)
viewModel.selectedItem.dy.subscribe((val)=>{ if ( val !== undefined ) viewModel.selectedItem.yset(undefined )}, this)

viewModel.workspace.indicator.subscribe((val)=>{ sendCommand('workspace.indicator', val) }, this)
viewModel.workspace.workspaceOrigin.x.subscribe(()=>{ sendCommand('workspace.origin', [parseFloat(viewModel.workspace.workspaceOrigin.x()), parseFloat(viewModel.workspace.workspaceOrigin.y())]) }, this)
viewModel.workspace.workspaceOrigin.y.subscribe(()=>{ sendCommand('workspace.origin', [parseFloat(viewModel.workspace.workspaceOrigin.x()), parseFloat(viewModel.workspace.workspaceOrigin.y())]) }, this)
viewModel.workspace.items.extend({ rateLimit: 100 })

viewModel.profile.name.subscribe(taskSave)
viewModel.tasks.extend({ rateLimit: 100 })

function init() {

/* TODO remove
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
*/

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
// TODO	if ( viewModel.touchMode() ) viewModel.dialog.fullscreen(true)
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
