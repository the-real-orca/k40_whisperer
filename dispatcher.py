
# import laser application modules
from config_manager import *
from file_manager import FileManager
from task_manager import TaskManager
from workspace import Workspace

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
configTasks(taskmanager)


def getStatus():
	payload = {
		"status": {
			"laser": laser.isActive(),
			"usb": laser.isInit(),
			"airassist": 0,
			"waterTemp": 0,
			"waterFlow": 0,
		},
		"alert": {
			"laser": False,
			"usb": not(laser.isInit()),
			"airassist": False,
			"waterTemp": False,
			"waterFlow": False
		},
		"message": laser.msg,
		"pos": {
			"x": laser.x,
			"y": laser.y
		},
		"workspace": workspace.toJson(),
		"tasks": taskmanager.toJson()
	}
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
		"workspace.set": workspace.setParams,
		"workspace.indicator": workspace.setIndicator,
		"workspace.origin": workspace.setWorkspaceOrigin,
		"item.set": workspace.setParams,
		"task.set": taskmanager.setParams,
		"task.run": taskmanager.run
	}

	# handle command
	try:
		# execute command
		cmdName = str(cmd.lower())
		print(cmdName, params)
		if params is None:
			commands[cmdName]()
		else:
			commands[cmdName](params)
	except Exception as e:
		print("Exception", e)
