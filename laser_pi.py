#!/usr/bin/python


import sys
import time
from nano_library import K40_CLASS


#    def Initialize_Laser():
k40=K40_CLASS()
try:
    print ("INIT:")
    k40.initialize_device()
    print ("DATA:")
    print (k40.read_data())
    print ("HELLO:")
    print (k40.say_hello())
    print ("HOME:")
    print (k40.home_position())
    print (k40.read_data())
#			self.laserX  = 0.0
#			self.laserY  = 0.0
        
    print ("MOVE")
    print (k40.rapid_move(10/25.4,0))
    time.sleep(5)
    print (k40.read_data())
    print ("UNLOCK:")
    print (k40.unlock_rail())
    print ("RELEASE:")
    print (k40.release_usb())

except StandardError as e:
#		except RuntimeError as e: #(RuntimeError, TypeError, NameError, StandardError):
    error_text = "%s" %(e)
    if "BACKEND" in error_text.upper():
        error_text = error_text + " (libUSB driver not installed)"
    print ("USB Error: %s" %(error_text))
    k40=None
    sys.exit()

except:
    print("Unknown USB Error")
    k40=None
    sys.exit()
                

print ("DONE")
