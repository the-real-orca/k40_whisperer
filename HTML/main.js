
ko.observableArray.fn.pushAll = function(valuesToPush) {
    var underlyingArray = this();
    this.valueWillMutate();
    ko.utils.arrayPushAll(underlyingArray, valuesToPush);
    this.valueHasMutated();
    return this;  //optional
};

var freeze = 0;

function jsonGet(name, callback) {
/* todo	
	$.get("/laser/" + name, function(data) {
		viewModel.network(true);
		if ( callback )
			callback( JSON.parse(data) )
	});
*/	
}

function jsonSet(name, val, callback) {
	var req = {
		type: 'PUT',
		url: "/laser/" + name,
		data: JSON.stringify(val),
		contentType: "application/json"
	}
	freeze++;
	req.success = function(data) {
		viewModel.network(true);
		freeze--;
		if ( callback )
			callback( JSON.parse(data) )
	}
	$.ajax(req)
}

var viewModel = {
	status: ko.observable("off"),
	intensity: ko.observable(1),
	focus: ko.observable(0),
	pos: {
		x: ko.observable(0),
		y: ko.observable(0)
	},
	timeLeft: ko.observable("---"),
	progress: ko.observable("---"),
	network: ko.observable(true),
	preview: ko.observable(),
	powerOn: function() { jsonSet("power", 1, viewModel.status) },
	powerOff: function() { jsonSet("power", 0, viewModel.status) },
	focusOn: function() { jsonSet("focus", "on") },
	focusOf: function() { jsonSet("focus", "off") },
	focusUp: function() { jsonSet("focus", -1) },
	focusDown: function() { jsonSet("focus", 1) },
	focusStop: function() { jsonSet("focus", 0) },
	focusAuto: function() { jsonSet("focus", "auto") }
};

var neje = {
	start: function() { 
		jsonSet("control", "start", viewModel.status);
		$(".tabs > .title[for='Live']").trigger("click");
	},
	pause: function() { jsonSet("control", "pause", viewModel.status) },
	reset: function() { jsonSet("control", "reset", viewModel.status) },
	setIntensity: function() { jsonSet("intensity", parseInt(viewModel.intensity()), viewModel.intensity) },
	previewTopLeft: function() { jsonSet("preview", "origin", viewModel.preview) },
	previewCenter: function() { jsonSet("preview", "center", viewModel.preview) },
	previewBox: function() { jsonSet("preview", "box", viewModel.preview) },
	moveUp: function() { jsonSet("move/y", 1) },
	moveDown: function() { jsonSet("move/y", -1) },
	moveLeft: function() { jsonSet("move/x", -1) },
	moveRight: function() { jsonSet("move/x", 1) }
}

var imgCounter = 1;
var imgLoading = 0;

function fxFadeIn(elem) {
	if (elem.nodeType === 1) {
		$(elem).addClass("fadeIn").on('animationend webkitAnimationEnd', function(){ $(elem).removeClass("fadeIn")});
	}
}
function fxSlideUpRemove(elem) {
	if (elem.nodeType === 1) {
		$(elem).addClass("slideUp").on('animationend webkitAnimationEnd', function(){ $(elem).remove(); });
	}
}

function init() {
	
	// init image dropper
	document.addEventListener("DOMContentLoaded", function() {
	  [].forEach.call(document.querySelectorAll('.dropimage'), function(img){
		$("#uploadImageBtn").addClass("disabled");
		img.onchange = function(e){
		  var inputfile = this, reader = new FileReader();
		  $(this).addClass("changed");
		  $("#uploadImageBtn").removeClass("disabled");
		  reader.onloadend = function(){
			inputfile.style['background-image'] = 'url('+reader.result+')';
		  }
		  reader.readAsDataURL(e.target.files[0]);
		}
	  });
	});
	
	// add pressed / released events for buttons
	var eventPressed = null;
	$('button, .button').on('touchstart', function(e) { 
		if ( eventPressed ) {
			if ( eventPressed.target == e.target )		// ignore multiple events on same target
				return;									
			$(eventPressed.target).trigger('released');	// release previous element
		}
		eventPressed = e;
		$(e.target).trigger('pressed', e);
	})
	$(document).on('touchend', function(ex) {
		if ( !eventPressed )
			return;
		$(eventPressed.target).trigger('released', ex); 
		eventPressed = null;
	})	
	$('button, .button').on('mousedown', function(e) { 
		if ( eventPressed ) {
			if ( eventPressed.target == e.target )		// ignore multiple events on same target
				return;									
			$(eventPressed.target).trigger('released');	// release previous element
		}
		eventPressed = e;
		if ( e.button == 0 ) {$(e.target).trigger('pressed', e);} // react on left mouse button
	})
	$(document).on('mouseup', function(ex) {
		if ( !eventPressed )
			return;
		$(eventPressed.target).trigger('released', ex); 
		eventPressed = null;
	})
	
	$('button, .button').on('keypress', function(e) { if ( e.key == ' ' || e.keyCode == 32 ) {$(e.target).trigger('pressed', e);} })
	$('button, .button').on('keyup', function(e) { if ( e.key == ' ' || e.keyCode == 32 ) {$(e.target).trigger('released', e);} })		
	
	// init tabs
	init_tabs();
	
	// init messages
	init_msg();
	
	// show message on network error
	$(document).on('ajaxError', function(xhr, options, error) {
		if ( viewModel.network() ) {
			viewModel.network(false);
			add_msg('error', 'network error ', 'communication error: ' + error, 5);
		}
	})	
	
	// bind model
	ko.applyBindings(viewModel);

	// bind live image update
	$(".liveImage")
		.on('load', function() { imgCounter++; })
		.on('error', function() { imgCounter++; console.log("error loading live image"); viewModel.network(false); })
	

	// bind drop image update
	$("#uploadImageFile").closest(".dropimage")
		.on('load', function() { 
			$("#uploadImageFile").closest(".dropimage").dropImage.removeClass("uploading"); 
		})
		.on('error', function() {
			console.log("error loading drop image"); 
			$("#uploadImageFile").closest(".dropimage").dropImage.removeClass("uploading");
			viewModel.network(false); 
		})
	
	

	// activate periodical update
	setInterval(update, 300);
	update();
}


function uploadImage() {

	var file = $("#uploadImageFile")[0].files[0];
	
	// check that file ia an image
	if (!file) {
		add_msg('error', 'upload error', 'no image selected');
		return;
	}
	if (!file.type.match(/image.*/)) {
		add_msg('error', 'upload error', 'Selected file is no valid image.<br> Supported image types are <b>JPEG</b> or <b>PNG</b>');
		return;
	}
		

	// indicate uploading
	var dropImage = $("#uploadImageFile").closest(".dropimage");
	dropImage.addClass("uploading");
	$("#uploadImageBtn").addClass("disabled");

	// build form data object
	var fd = new FormData();
	fd.append('upload', file); // append the file
    $.ajax({
        url: '/upload',
        type: 'POST',
        success: function(data) {
			dropImage.removeClass("changed")
				.css('background-image', "url(uploads/mask.png?t="+ Date.now() +")");
			$("#UploadImage .next").removeClass("disabled");
			dropImage.removeClass("uploading");
        },
        error: function() {
			add_msg('error', "upload error", "cannot uploade image: " + data);
			dropImage.removeClass("changed");
			dropImage.removeClass("uploading");
        },
        data: fd,
        contentType: false,
        processData: false,
        cache: false
    });
}
	

function update() {

	if ( !viewModel.network() )	// skip on network failure
		return;	
		
	// query laser status
	if ( !freeze ) {
		jsonGet("status", function(data) {
			viewModel.status(data.status);
			viewModel.intensity(data.intensity);
			viewModel.pos.x(data.pos.x);
			viewModel.pos.y(data.pos.y);
			viewModel.timeLeft(data.timeLeft);
			viewModel.progress(data.progress);
		});
	}
	
	// fetch new live image
	if ( imgLoading < imgCounter ) {
		imgLoading = imgCounter;
		$(".liveImage").attr("src", "laser/image.jpg?t=" + Date.now());
	}
	
	// fetch new focus image if focus tab is active
	if ( $("#Focus").hasClass("active") ) {
		$(".focusImage").attr("src", "laser/focus.jpg?t=" + Date.now());

		// update focus data
		$.getJSON("laser/focus", function(data, status, xhr) {
			if ( xhr.status == 200 && data ){
				// decode data
				viewModel.focus(data.focus );
			} else {
				// error
				if ( viewModel.network() ) {
					viewModel.network(false);
					add_msg('warning', "network error", "cannot read meta data: " + xhr.statusText, 5);
				}
			}
		});

	}
	
}
