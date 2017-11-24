from task_manager import Task
import design_utils as design

# import laser communication
import k40_wrapper
import laser_emulator

config = {
		'workspace': {
					'homePos': [-150,100],
					'size': [300, 200]
				},
		'tasks': [
					{'id': "engrave", "colors": [design.BLUE], "speed": 100, "type": Task.VECTOR},
					{'id': "cut", "colors": [design.BLACK, design.RED], "speed": 50, "type": Task.VECTOR}
				],
		'laser': {
#					'type': k40_wrapper		# K40 China Laser
					'type': laser_emulator	# Simulated Laser for Testing
				}
		}

def configLaser():
	laser = config['laser']['type'].LASER_CLASS()
	return laser
		
		
def configTasks(taskmanager):
	try:
		del taskmanager.tasks[:]
		for task in config['tasks']:
			taskmanager.tasks.append( Task(id=task['id'], colors=task['colors'], speed=task['speed'], type=task['type']) )
	except:
		print("task config error")

def configWorkspace(workspace):
	try:
		workspace.homePos = config['workspace']['homePos']
		workspace.size = config['workspace']['size']
		workspace.update()
	except:
		print("workspace config error")
