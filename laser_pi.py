

    def Initialize_Laser():
        k40=K40_CLASS()
        try:
            k40.initialize_device()
            k40.read_data()
            k40.say_hello()
			k40.home_position()
			self.laserX  = 0.0
			self.laserY  = 0.0
		
        except StandardError as e:
            error_text = "%s" %(e)
            if "BACKEND" in error_text.upper():
                error_text = error_text + " (libUSB driver not installed)"
            statusMessage.set("USB Error: %s" %(error_text))
            statusbar.configure( bg = 'red' )
            k40=None
            debug_message(traceback.format_exc())

        except:
            statusMessage.set("Unknown USB Error")
            statusbar.configure( bg = 'red' )
            k40=None
            debug_message(traceback.format_exc())
			
			