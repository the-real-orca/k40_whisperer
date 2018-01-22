
var updateInterval = 200

function clone(obj) {
	return JSON.parse(JSON.stringify(obj));
}

function roundTo(val, fraction=0.01) {
    return Math.round(val / fraction) * fraction
}

function uuid() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
	var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
	return v.toString(16);
  });
}

ko.options.deferUpdates = true;
ko.dirtyFlag = function(root) {
	var dirtyFlag = ko.computed(function() {
		var state = ko.toJSON(root)
		if ( dirtyFlag ) {
			var dirty = dirtyFlag._initialState() != state
			if ( dirty && !dirtyFlag._dirtyCache && dirtyFlag._onDirty )
				dirtyFlag._onDirty()
			dirtyFlag._dirtyCache = dirty
			return dirty
		}
		return false
	})
	dirtyFlag._initialState = ko.observable()
	dirtyFlag._onDirty = null
	dirtyFlag._dirtyCache = false
	dirtyFlag.reset = function() {
		dirtyFlag._initialState( ko.toJSON(root) )
	}
	dirtyFlag.onDirty = function(callback) {
		dirtyFlag._onDirty = callback
	}

	dirtyFlag.reset()
	return dirtyFlag
}
ko.observableArray.fn.pushAll = function(valuesToPush) {
	var underlyingArray = this()
	this.valueWillMutate()
	ko.utils.arrayPushAll(underlyingArray, valuesToPush)
	this.valueHasMutated()
	return this  //optional
};
ko.observableArray.fn.move = function(from, to){
	this.valueWillMutate();
	this.peek().splice(to, 0, this.peek().splice(from, 1)[0]);
	this.valueHasMutated();
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
		var precision = ko.utils.unwrapObservable(allBindingsAccessor().precision)
		if (precision === undefined)
			precision = ko.bindingHandlers.numericValue.defaultPrecision
		try {
			element.textContent = value.toFixed(precision)
		} catch (e) {
			element.textContent = "";
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
function moveWorkspaceOriginX(dx) {
	var x = parseFloat(viewModel.workspace.workspaceOrigin.x()) + parseFloat(dx)*viewModel.config.stepSize()
	viewModel.workspace.workspaceOrigin.x(x)
	return true
}
function moveWorkspaceOriginY(dy) {
	var y = parseFloat(viewModel.workspace.workspaceOrigin.y()) + parseFloat(dy)*viewModel.config.stepSize()
	viewModel.workspace.workspaceOrigin.y(y)
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

function itemsMergeWithSelected(item, selected) {		
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
	var selected = viewModel.selectedItems;

	// reset selected items display
	selected.name('')
	selected.x(null)
	selected.y(null)
	selected.width(null)
	selected.height(null)
	selected.viewBox(null)
	selected.boundingBox(null)
	selected.color(null)	

	// merge with selected items
	for (var i=0; i < viewModel.workspace.items().length; i++) {
		var item = viewModel.workspace.items()[i]
		if ( index !== undefined )
			item.selected(index==i)
		if ( item.selected() ) {
			itemsMergeWithSelected(item, selected)
		}
	}

	// set helper data
	selected.ax(selected.x())
	selected.ay(selected.y())
	selected.dx(undefined)
	selected.dy(undefined)
	selected.showAbs(true)

console.log("itemPrepareParams")
	viewModel.dirty.selectedItems.reset()
	return true
}
function itemsSaveSelected() {
	var selected = viewModel.selectedItems
	var params = ko.toJS(viewModel.selectedItems)
	if ( params.ax !== undefined ) {
		params.x = params.ax
		params.dx = 0
	}
	if ( params.ay !== undefined ) {
		params.y = params.ay
		params.dy = 0
	}
	viewModel.dirty.selectedItems.reset()

	itemsSendCmdToSelected('items.set', params)

console.log("itemsSaveSelected")
	return true
}

function itemsRotateSelected(angle) {
	itemsSendCmdToSelected('items.rotate', {angle: angle})
	return true
}

function itemsMirrorSelected(line) {
	itemsSendCmdToSelected('items.mirror', {mirror: line})
	return true
}

function itemsSendCmdToSelected(cmd, params) {
	var cmds = []
	var itemsList = viewModel.workspace.items()
	for (var i=0; i<itemsList.length; i++) {
		var item = itemsList[i]
		if ( item.selected() ) {
			params.id = item.id()
			params.name = item.name()
			cmds.push( prepareCommand(cmd, clone(params)) )
		}
	}
	return sendCommand(cmds)
}

function setActiveProfile(id) {
	id = ko.utils.unwrapObservable(id)
	if ( !id ) {
		// create new profile
		id = uuid()
	}
	sendCommand('profile.setactive', {id: id})
	// close dialog
	viewModel.dialog.profilesList(false)
}
function removeProfile(id) {
	id = ko.utils.unwrapObservable(id)
	sendCommand('profile.remove', id)
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
		tasks: ko.toJS(viewModel.tasks)
	}
	viewModel.dirty.profile.reset()
	viewModel.dirty.tasks.reset()

	sendCommand('profile.setactive', params)
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
	viewModel.selectedItems.ax(0); viewModel.selectedItems.ay(0)
	viewModel.selectedItems.showAbs(true)
}
function alignAboveOfAxis() {
	var delta = -viewModel.selectedItems.boundingBox()[1]
	viewModel.selectedItems.dy(delta)
	viewModel.selectedItems.showAbs(false)
}
function alignUnderAxis() {
	var delta = -viewModel.selectedItems.boundingBox()[3]
	viewModel.selectedItems.dy(delta)
	viewModel.selectedItems.showAbs(false)
}
function alignLeftOfAxis() {
	var delta = -viewModel.selectedItems.boundingBox()[2]
	viewModel.selectedItems.dx(delta)
	viewModel.selectedItems.showAbs(false)
}
function alignRightOfAxis() {
	var delta = -viewModel.selectedItems.boundingBox()[0]
	viewModel.selectedItems.dx(delta)
	viewModel.selectedItems.showAbs(false)
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
	viewModel.expectedSeqNr = viewModel.seqNr +1
	console.log("sending ...", data)
	$.ajax({
		type: 'POST',
		url: '/command',
		data: JSON.stringify(data),
		dataType: 'application/json',
		timeout: 1000,
		success: function(data) {
			updateStatus(data)
		},
		error: function(xhr, type) {
			viewModel.status.network(false)
			viewModel.alert.network(true)
			viewModel.expectedSeqNr = viewModel.seqNr
		}
	})
	return true

}
function profileViewModel(data={}, profile) {
	if ( !data.id )
		data.id = uuid()
	if ( typeof profile == "object" ) {
		profile.id(data.id)
		if ( profile.name !== undefined )
			profile.name(data.name)
	} else {
		profile = {
			id: ko.observable(data.id),
			name: ko.observable(data.name),
		}
	}
	return profile
}
function taskViewModel(data={}, task) {
	if ( !data.id )
		data.id = uuid()
	if ( typeof task == "object" ) {
		task.id(data.id)
		if ( data.name !== undefined )
			task.name(data.name)
		if ( data.colors !== undefined && JSON.stringify(data["colors"]) != JSON.stringify(task.colors()) ) // workaround: update on actual change only
			task.colors(data.colors)
		if ( data.speed !== undefined )
			task.speed( parseFloat(data.speed) )
		if ( data.intensity !== undefined )
			task.intensity( parseFloat(data.intensity) )
		if ( data.type !== undefined )
			task.type(data.type)
		if ( data.repeat !== undefined )
			task.repeat( parseInt(data.repeat) )
		if ( data.status !== undefined )
			task.status(data.status)
		if ( data.progress !== undefined )
			task.progress( parseFloat(data.progress) )
	} else {
		task = {
			id: ko.observable(data.id),
			name: ko.observable(data.name),
			colors: ko.observable(data.colors),
			speed: ko.observable(data.speed),
			intensity: ko.observable(data.intensity),
			type: ko.observable(data.type),
			repeat: ko.observable(data.repeat),
			status: ko.observable(data.status),
			progress: ko.observable(data.progress),
			selected: ko.observable(true)
		}
		task._ = ()=>{} // dummy function to hide private elements from JSON
		task._.statusIcon = ko.pureComputed(function() { return taskStatusIcon(this.status()) }, task),
		task._.statusColor = ko.pureComputed(function() { return taskStatusColor(this.status()) }, task),
		task._.showMenu = ko.observable(false);
		task._.toggleMenu = ()=>{ task._.showMenu(task._.showMenu()) }
	}
	return task
}
function itemViewModel(data={}, item) {
	if ( !data.id )
		data.id = uuid()
	if ( typeof item == "object" ) {
		item.id(data.id)
		if ( data.name !== undefined )
			item.name(data.name)
		if ( data.color !== undefined )
			item.color(data.color)
		if ( data.x !== undefined )
			item.x( parseFloat(data.x) )
		if ( data.y !== undefined )
			item.y( parseFloat(data.y) )
		if ( data.width !== undefined )
			item.width( parseFloat(data.width) )
		if ( data.height !== undefined )
			item.height( parseFloat(data.height) )
		if ( data.viewBox !== undefined && JSON.stringify(data["viewBox"]) != JSON.stringify(item.viewBox()) ) // workaround: update on actual change only
			item.viewBox( data.viewBox )
		if ( data.boundingBox !== undefined  && JSON.stringify(data["boundingBox"]) != JSON.stringify(item.boundingBox()) ) // workaround: update on actual change only
			item.boundingBox(data.boundingBox)
		if ( data.url !== undefined )
			item.url( data.url )
	} else {
		item = {
			id: ko.observable(data.id),
			name: ko.observable(data.name),
			color: ko.observable(data.color),
			x: ko.observable(parseFloat(data.x)),
			y: ko.observable(parseFloat(data.y)),
			width: ko.observable(parseFloat(data.width)),
			height: ko.observable(parseFloat(data.height)),
			viewBox: ko.observable(data.viewBox),
			boundingBox: ko.observable(data.boundingBox),
			url: ko.observable(data.url),
			selected: ko.observable(true)
		}
	}
	return item
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
function updateStatus(received) {

	if ( typeof received == "string" )
		received = JSON.parse(received)

	if ( viewModel.expectedSeqNr > received.seqNr ) {
		// ignore status update (expect higher sequence number)
		return
	}

	viewModel.instable = true

	// update status
	if ( typeof received.status == "object" ) {
		for ( var key in received.status )
			viewModel.status[key]( received.status[key] )
	}
	if ( typeof received.alert == "object" ) {
		for ( var key in received.alert )
			viewModel.alert[key]( received.alert[key] )
	}

	// update position
	if ( typeof received.pos == "object" ) {
		var x = parseFloat(received.pos.x), y = parseFloat(received.pos.y)
		if ( isNaN(x) || isNaN(y) ) {
			viewModel.pos.valid(false)
		} else {
			viewModel.pos.valid(true)
			viewModel.pos.x(x)
			viewModel.pos.y(y)
		}
	}

/* TODO
	// update message
	if ( typeof received.message == "string" ) {
		viewModel.message( received.message )
	}
*/

	// update workspace
	if ( "workspace" in received ) {
		if ( "width" in received.workspace )
			viewModel.workspace.width( received.workspace["width"] )
		if ( "height" in received.workspace )
			viewModel.workspace.height( received.workspace["height"] )
		if ( "homePos" in received.workspace ) {
			viewModel.workspace.homePos.x( received.workspace["homePos"][0] )
			viewModel.workspace.homePos.y( received.workspace["homePos"][1] )
		}
		if ( "workspaceOrigin" in received.workspace ) {
			viewModel.workspace.workspaceOrigin.x( received.workspace["workspaceOrigin"][0] )
			viewModel.workspace.workspaceOrigin.y( received.workspace["workspaceOrigin"][1] )
		}

		if ( "indicator" in received.workspace)
			viewModel.workspace.indicator( received.workspace["indicator"] )

		if ( "viewBox" in received.workspace && JSON.stringify(received.workspace["viewBox"]) != JSON.stringify(viewModel.workspace.viewBox()) )
			viewModel.workspace.viewBox( received.workspace["viewBox"] )


		if ( received.workspace.items instanceof Array ) {
			var items = viewModel.workspace.items()

			// prepare items list
			for ( var i = 0; i < items.length; i++ ) {
				var item = items[i]
				item.remove = true
			}

			// update with received items
			for ( var i = 0; i < received.workspace.items.length; i++ ) {
				var json = received.workspace.items[i]
				for ( var i = 0; i < items.length; i++ )
					if (items[i].id() == json.id) {
						// item found -> update
						var item = items[i]
						itemViewModel(json, item)
						item.remove = false
						item.index = i;
						break
					}
				if ( i == items.length ) {
					// new task -> append
					var item = itemViewModel(json);
					item.index = i;
					viewModel.workspace.items.push(item)
				}
			}

			// clean-up
			viewModel.workspace.items.remove((item)=>{ return item.remove })

            // sort by index
            viewModel.workspace.items.sort((left, right)=>{ return left.index < right.index ? -1 : 1 })

			// update selected items
			if ( viewModel.dialog.itemsSettings() && viewModel.dirty.workspace() ) {
				itemPrepareParams()
			}
		}

		viewModel.dirty.workspace.reset()
	}

	// update profiles / tasks
	if ( "profile" in received ) {
		if ( received.profile.profiles instanceof Array ) {
			var profiles = viewModel.profile.list()
			// prepare task list
			for ( var i = 0; i < profiles.length; i++ )
				profiles[i].remove = true

			// update with received profiles
			for ( var i = 0; i < received.profile.profiles.length; i++ ) {
				var json = received.profile.profiles[i]
				for ( var i = 0; i < profiles.length; i++ )
					if ( profiles[i].id() == json.id ) {
						// profile found -> update
						var profile = profiles[i]
						profileViewModel(json, profile)
						profile.remove = false
						profile.index = i;
						break
					}
				if ( i == profiles.length ) {
					// new profile -> append
					var profile = profileViewModel(json)
					profile.index = i;
					viewModel.profile.list.push(profile)
				}
			}

			// clean-up
			viewModel.profile.list.remove((item)=>{ return item.remove })

            // sort by index
            viewModel.profile.list.sort((left, right)=>{ return left.index < right.index ? -1 : 1 })
		}

		if ( "active" in received.profile ) {
			var profile = received.profile.active

			if ( !profile ) {
				profile = {
					id: uuid(),
					name: "",
					tasks: []
				}
			}

			// active profile
			viewModel.profile.id( profile["id"] )
			if ( "name" in profile )
				viewModel.profile.name( profile["name"] )

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
						var task = taskViewModel(json)
						viewModel.tasks.push(task)
					}
				}

				// clean-up
				viewModel.tasks.remove((item)=>{ return item.remove })
			}
			viewModel.dirty.tasks.reset()
			if ( viewModel.tasks().length == 0 ) {
				viewModel.tasks.push( taskViewModel({}) )
			}
		}
		viewModel.dirty.profile.reset()
	}

	// update sequence as final step to avoid data races
	// -> intermediate requests will be ignored due-to sequence error
	viewModel.seqNr = received.seqNr
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
var viewModel = {
	instable: false,
	touchMode: ko.observable(false),
	seqNr: 0,
	expectedSeqNr: 0,
	status: {
		laser: ko.observable(0),
		usb: ko.observable(false),
		airAssist: ko.observable(0),
		waterTemp: ko.observable(0),
		waterFlow: ko.observable(0),
		network: ko.observable(false),
		networkIcon: ko.pureComputed(function() { return viewModel.status.network() ? "icon-lan-connect" : "icon-lan-disconnect"; }),
		fullscreen: ko.observable(isFullscreen())
	},
	alert: {
		laser: ko.observable(false),
		usb: ko.observable(false),
		airAssist: ko.observable(false),
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
		stepSize: ko.observable(1)
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
		indicator: ko.observable(""),
		items: ko.observableArray()
	},
	pos: {
		valid: ko.observable(false),
		x: ko.observable(0),
		y: ko.observable(0)
	},
	profile: {
		id: ko.observable(),
		name: ko.observable(),
		selected: ko.observable(),
		list: ko.observableArray()
	},
	tasks: ko.observableArray(),
	selectedTask: ko.observable(),
	selectAllTasks: ko.pureComputed({
		read: function() {
			selectedCount=0
			for ( var i = 0; i < viewModel.tasks().length; i++ ) {
				var task = viewModel.tasks()[i]
				if ( task.selected() )
					selectedCount++
			}
			return ( selectedCount == viewModel.tasks().length )
		},
		write: function(val) {
			for ( var i = 0; i < viewModel.tasks().length; i++ ) {
				var task = viewModel.tasks()[i]
				task.selected(val)
			}
		},
		owner: this
	}),
	selectedItems: {
		name: ko.observable(""),
		x: ko.observable(),
		y: ko.observable(),
		ax: ko.observable(),
		ay: ko.observable(),
		dx: ko.observable(0),
		dy: ko.observable(0),
		showAbs: ko.observable(true),
		width: ko.observable(),
		height: ko.observable(),
		viewBox: ko.observable(),
		boundingBox: ko.observable(),
		color: ko.observable()		
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
		fullscreen: ko.observable(false),
		itemsList: ko.observable(false),
		itemsSettings: ko.observable(false),
		profilesList: ko.observable(false),
		taskSettings: ko.observable(false),
		wait: ko.observable(false)
	},
	dirty: {}
};
// view model functions
viewModel.continue = function() { viewModel.dialog.wait(false) }

viewModel.workspace.indicator.subscribe((val)=>{ if (val && viewModel.dirty.workspace()) sendCommand('workspace.indicator', val) }, this)
viewModel.workspace.workspaceOrigin.x.subscribe(()=>{ if (viewModel.dirty.workspace()) sendCommand('workspace.origin', [parseFloat(viewModel.workspace.workspaceOrigin.x()), parseFloat(viewModel.workspace.workspaceOrigin.y())]) }, this)
viewModel.workspace.workspaceOrigin.y.subscribe(()=>{ if (viewModel.dirty.workspace()) sendCommand('workspace.origin', [parseFloat(viewModel.workspace.workspaceOrigin.x()), parseFloat(viewModel.workspace.workspaceOrigin.y())]) }, this)
viewModel.dirty.workspace = ko.dirtyFlag(viewModel.workspace);

// make sure that either dx/y or x/yset is valid
viewModel.selectedItems.ax.subscribe((val)=>{ if ( val !== undefined ) viewModel.selectedItems.dx(undefined) }, this)
viewModel.selectedItems.ay.subscribe((val)=>{ if ( val !== undefined ) viewModel.selectedItems.dy(undefined) }, this)
viewModel.selectedItems.dx.subscribe((val)=>{ if ( val !== undefined ) viewModel.selectedItems.ax(undefined) }, this)
viewModel.selectedItems.dy.subscribe((val)=>{ if ( val !== undefined ) viewModel.selectedItems.ay(undefined )}, this)
viewModel.dirty.selectedItems = ko.dirtyFlag(viewModel.selectedItems);
viewModel.dirty.selectedItems.onDirty( itemsSaveSelected )

viewModel.dirty.profile = ko.dirtyFlag(viewModel.profile);
viewModel.dirty.profile.onDirty( taskSave )
viewModel.dirty.tasks = ko.dirtyFlag(viewModel.tasks);
viewModel.dirty.tasks.onDirty( taskSave )

viewModel.dialog.itemsList.subscribe((val)=>{
	if ( val ) {
		var itemsList = viewModel.workspace.items()
		if ( itemsList.length == 1 ) {
			// skip items list, if we have only one item
			itemsList[0].selected(true)
			itemPrepareParams()
			viewModel.dialog.itemsList(false)
			viewModel.dialog.itemsSettings(true)
		}
	}
})


function init() {
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

	// init controllers
	gamepad.dx = 0; gamepad.dy = 0
	gamepad.init((gp, buttons, axes)=>{
		var mult = 4

		// implement dead-zone around neutral position
		var dead = 0.1
		var x = axes[0]
		var sign = x < 0 ? -1 : 1
		var dx = (sign*x) - dead
		if ( dx > 0 ) {
			dx = Math.pow(dx, 1.5) * mult * sign
		} else
			dx = 0
		var y = axes[1]
		sign = y < 0 ? -1 : 1
		var dy = (sign*y) - dead
		if ( dy > 0 ) {
			dy = -Math.pow(dy, 1.5) * mult * sign
		} else
			dy = 0
		gamepad.dx = dx
		gamepad.dy = dy

		if ( buttons[0] )
    		resetWorkspaceOrigin()
	})
	setInterval(()=>{
		if ( gamepad.dx || gamepad.dy ) {
			console.log(gamepad.dx, gamepad.dy)
			viewModel.workspace.workspaceOrigin.x( roundTo(viewModel.workspace.workspaceOrigin.x() + gamepad.dx, 0.1) )
			viewModel.workspace.workspaceOrigin.y( roundTo(viewModel.workspace.workspaceOrigin.y() + gamepad.dy, 0.1) )
		}
	}, 250)


	// periodic status request
	getStatus()
	setInterval(getStatus, updateInterval)

	// determine to switch to fullscreen mode
	document.addEventListener('fullscreenchange', fullscreenEventHandler, false);
	document.addEventListener('webkitfullscreenchange', fullscreenEventHandler, false);
	document.addEventListener('mozfullscreenchange', fullscreenEventHandler, false);
	document.addEventListener('MSFullscreenChange', fullscreenEventHandler, false);
	viewModel.touchMode('ontouchstart' in window || navigator.msMaxTouchPoints || window.screen.width <= 1024)
    if ( viewModel.touchMode() ) viewModel.dialog.fullscreen(true)
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
}
		document.webkitExitFullscreen();
	}
