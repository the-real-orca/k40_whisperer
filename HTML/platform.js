

function testPlatform() {
	return "NodeJS";
}

var Platform = {
	type: testPlatform(),
	isNodeJS: ( testPlatform() == 'NodeJS' ), // TODO
	isESP8266: ( testPlatform() == 'ESP8266' )
}

// platform specific setup	
if ( Platform.isESP8266 ) {
	var wifi = require("Wifi");
	wifi.connect("my-ssid", {password:"my-pwd"}, function(ap){ 
		this.log("connected:", ap); });
	wifi.stopAP();
}

Platform.require = function(module) {
	return require(module);
}
	

Platform.log = function(str) {
	if ( this.isNodeJS ) {
		console.log(str);
	}
}	

module.exports = Platform;
