
var gamepad = {
	handle: null,
	state: {
		buttons: [false,false,false,false],
		axes: [0,0]
	}
}

gamepad.init = function(onChange, interval=100) {
	window.addEventListener("gamepadconnected", function(e) {
		console.log("Gamepad connected at index %d: %s. %d buttons, %d axes.", e.gamepad.index, e.gamepad.id, e.gamepad.buttons.length, e.gamepad.axes.length);
		clearInterval(gamepad.handle)
		gamepad.handle = setInterval(()=>{
				var gp = navigator.getGamepads()[0]
				if ( gp ) {
					var oldState = gamepad.state
					var newState = {
						buttons: [false,false,false,false],
						axes: [0,0]
					}
					var changed = false

					// buttons
					for (var i=0; i<newState.buttons.length; i++) {
						var b = gp.buttons[i]
						if ( typeof(b) == "object" )
							newState.buttons[i] = b.pressed
						else
							newState.buttons[i] = (b == 1.0)
						if ( newState.buttons[i] != oldState.buttons[i] )
							changed = true
					}
					// axes
					for (var i=0; i<newState.axes.length; i++) {
						newState.axes[i] = Math.round(gp.axes[i]* 1000)/1000
						if ( newState.axes[i] != oldState.axes[i] )
							changed = true
					}

					if ( changed ) {
    					gamepad.state = newState
						onChange(gp, newState.buttons, newState.axes)
					}
				}
			}, interval);
	});
	window.addEventListener("gamepaddisconnected", function(e) {
		console.log("Gamepad disconnected from index %d: %s", e.gamepad.index, e.gamepad.id);
		clearInterval(gamepad.handle)
	});
}
