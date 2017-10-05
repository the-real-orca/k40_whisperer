#!/usr/bin/env python

import asyncio
import datetime
import random
import websockets

async def time(websocket, path):
    while True:
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        await websocket.send(now)
        await asyncio.sleep(random.random() * 3)

start_server = websockets.serve(time, '127.0.0.1', 5678)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()


# Common patterns
async def handler(websocket, path):
    consumer_task = asyncio.ensure_future(consumer_handler(websocket))
    producer_task = asyncio.ensure_future(producer_handler(websocket))
    done, pending = await asyncio.wait(
        [consumer_task, producer_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in pending:
        task.cancel()
		

<!DOCTYPE html>
<html>
    <head>
        <title>WebSocket demo</title>
    </head>
    <body>
        <script>
            var ws = new WebSocket("ws://127.0.0.1:5678/"),
                messages = document.createElement('ul');
            ws.onmessage = function (event) {
                var messages = document.getElementsByTagName('ul')[0],
                    message = document.createElement('li'),
                    content = document.createTextNode(event.data);
                message.appendChild(content);
                messages.appendChild(message);
            };
            document.body.appendChild(messages);
        </script>
    </body>
</html>



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
			
			