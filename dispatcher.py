
import logging

# import laser application modules
from config_manager import *
from file_manager import FileManager
from task_manager import TaskManager
from workspace import Workspace
from sensor_arduino import Sensor

def NullFunc():
	return

laser = configLaser()

# init file manager
filemanager = FileManager(rootPath = COMPUTED_FOLDER, webRootPath = HTML_FOLDER)
configFileManager(filemanager)

# init workspace
workspace = Workspace(filemanager = filemanager, laser = laser)
configWorkspace(workspace)

# init task manager
taskmanager = TaskManager(laser, workspace)
loadProfiles(taskmanager)

# init sensor
sensor = Sensor(config['sensor']['config']['port'], config['sensor']['config']['baud'], indexMap=config['sensor']['indexMap'])


def getStatus():
	sensor.update()
	payload = {
		"status": {
			"laser": laser.isActive(),
			"usb": laser.isInit(),
			"airAssist": sensor.airAssist.val,
			"waterTemp": sensor.waterTemp.val,
			"waterFlow": sensor.waterFlow.val
		},
		"alert": {
			"laser": sensor.general.alert,
			"usb": not(laser.isInit()),
			"airAssist": False,
			"waterTemp": sensor.waterTemp.alert,
			"waterFlow": sensor.waterFlow.alert
		},
		"message": laser.msg,
		"pos": {
			"x": laser.x,
			"y": laser.y
		},
		"workspace": workspace.toJson(),
		"profile": taskmanager.toJson()
	}
	payload['debug'] = laser.msg # TODO log.getHistory(10)
	return payload


def dispatchCommand(cmd, params = None):
	commands = {
		"status": NullFunc,
		"init": laser.init,
		"release": laser.release,
		"home": laser.home,
		"unlock": laser.unlock,
		"stop": laser.stop,
		"move": lambda params: laser.move(float(params.get("dx", 0)), float(params.get("dy", 0))),
		"moveto": lambda params: laser.moveTo(float(params.get("x", 0)), float(params.get("y", 0))),
		"workspace.load": workspace.load,
		"workspace.clear": workspace.clear,
		"workspace.remove": workspace.remove,
		"workspace.indicator": workspace.setIndicator,
		"workspace.origin": workspace.setWorkspaceOrigin,
		"workspace.set": workspace.setParams,
		"items.set": workspace.itemSetParams,
		"items.rotate": workspace.itemRotate,
		"items.mirror": workspace.itemMirror,
		"profile.setactive": lambda params: taskmanager.setActiveProfile(params) or saveProfiles(taskmanager),
		"profile.remove": lambda params: taskmanager.removeProfile(params) or saveProfiles(taskmanager),
		"profile.run": taskmanager.run
	}

	# handle command
	try:
		# execute command
		cmdName = str(cmd.lower())
		logging.info("dispatchCommand: " + cmdName + " -> " + str(params))
		if params is None:
			commands[cmdName]()
		else:
			commands[cmdName](params)
	except Exception as e:
		logging.error("Exception: " + str(e))
