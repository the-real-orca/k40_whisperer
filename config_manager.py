from task_manager import Profile, Task
import design_utils as design

# import laser communication
import k40_wrapper
import laser_emulator

# web server configuration
HTML_FOLDER = 'HTML'
UPLOAD_FOLDER = HTML_FOLDER + '/uploads'
COMPUTED_FOLDER = HTML_FOLDER + '/computed'
ALLOWED_EXTENSIONS = set(['dxf']) # TODO set(['svg', 'dxf', 'png', 'jpg', 'jpeg'])
MAX_CONTENT_LENGTH = 64 * 1024 * 1024

config = {
		'workspace': {
			'home': 'top-left', # top-left, top-right, bottom-left, bottom-right
			'homeOff': [0,0],
			'size': [300, 200]
		},
		'profiles': [
			{
				'id': "sample",
				'name': "sample",
				'tasks': [
					{'id': "sample", 'colors': [design.BLUE], 'speed': 50, 'type': Task.VECTOR}
				]
			}, {
				'id': "test_1",
				'name': "test 3mm",
				'tasks': [
					{'id': "engrave", 'colors': [design.BLUE], 'speed': 50, 'type': Task.VECTOR},
					{'id': "cut", 'colors': [design.BLACK, design.RED], 'speed': 5, 'type': Task.VECTOR, 'repeat': 1}
				]
			}
		],
		'laser': {
#					'type': k40_wrapper		# K40 China Laser
					'type': laser_emulator	# Simulated Laser for Testing
				}
}

def configLaser():
	laser = config['laser']['type'].LASER_CLASS()
	return laser
		
def configFileManager(filemanager):
	# nothing to do
	pass

def configTasks(taskmanager):
	try:
		taskmanager.profiles.clear()
		for profile in config['profiles']:
			taskmanager.setProfile( profile )
	except:
		print("task config error")

def configWorkspace(workspace):
	try:
		workspace.home = config['workspace']['home']
		workspace.homeOff = config['workspace']['homeOff']
		workspace.size = config['workspace']['size']
		workspace.defaultOrigin = config['workspace']['home']
		workspace.reset()
	except:
		print("workspace config error")
