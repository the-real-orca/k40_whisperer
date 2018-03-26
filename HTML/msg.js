function init_msg() {
	viewModel.msgList = ko.observableArray();
}

function add_msg(type, header, text, timeout) {
	var msg = {
		type: type || "default",
		header: header || "",
		text: text || "",
		stack: viewModel.msgList,
		timeoutHandle: ko.observable(null)
	}

	// remove function
	msg.removeTimeout = function() {
		if ( msg.timeoutHandle() )
			clearTimeout( msg.timeoutHandle() );
		msg.timeoutHandle(null);
	}	
	msg.remove = function() {
		msg.removeTimeout();
		msg.stack.remove(msg);
	}	
	
	// set timeout
	if ( timeout === undefined ) {
		if ( type == "error" || type == "warning" )
			msg.timeout = 0;
		else
			msg.timeout = 10;
	} else {
		msg.timeout = timeout;
	}
	if ( msg.timeout ) {
		msg.timeoutHandle(setTimeout( msg.remove, msg.timeout*1000 ));			
	} else 
		msg.timeoutHandle(null);
	
	viewModel.msgList.push(msg);
}