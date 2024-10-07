# Based on https://gist.github.com/aallan/3d45a062f26bc425b22a17ec9c81e3b6
# Turn on/off comments at the bottom to use standalone/as a module on pico W

import sys
sys.path.append("")

import time
import network
import asyncio
from machine import Pin
import config
import relay_controller

#open JSON file and load data if available
config.load_config()

ssid = '<SSID_here>'
password = '<wifi_password_here>'

wlan = network.WLAN(network.STA_IF) # set WiFi to station interface

def connect_to_network():
    global wlan

    max_try = 3 # Attempt to connect 3 times
    for i in range(max_try):
        wlan.active(False) # de-activate the network interface
        wlan.active(True) # activate the network interface
        wlan.config(pm = 0xa11140)  # Disable power-save mode
        wlan.connect(ssid, password) # connect to wifi network  
        max_wait = 10
        # wait for connection
        while max_wait > 0:
            """
                0   STAT_IDLE -- no connection and no activity,
                1   STAT_CONNECTING -- connecting in progress,
                -3  STAT_WRONG_PASSWORD -- failed due to incorrect password,
                -2  STAT_NO_AP_FOUND -- failed because no access point replied,
                -1  STAT_CONNECT_FAIL -- failed due to other problems,
                3   STAT_GOT_IP -- connection successful.
            """
            if wlan.status() < 0 or wlan.status() >= 3:
                # connection successful
                break
            max_wait -= 1
            print('waiting for connection... ' + str(max_wait))
            time.sleep(1)

        # check connection
        if wlan.status() == 3:
            # Successful connection
            print('wlan connected')
            status = wlan.ifconfig()
            pico_ip = status[0]
            print('ip = ' + status[0])
            break
        else:
            print('failed connection, retrying...')
            # connection unsuccessful

async def serve_client(reader, writer):
    print("Client connected")

    line = ""
    request_array = []
    while line != b"\r\n":
        line = await reader.readline()
        if type(line) == str:
            request_array.append(line)
        elif type(line) == bytes:
            request_array.append(line.decode())

    print("ARRAY: ", request_array)
    request_line = request_array[0]
    print("Request: ", request_line)

    # if request_url.find("/ledon") != -1:
        # turn LED on
        # led_state = True
        # led.on()
    # elif request_url.find("/ledoff") != -1:
        # turn LED off
        # led_state = False
        # led.off()

    if request_line.find("/saveConfig") != -1:
        print("GET /saveConfig found")
        #url = "http://www.example.org/default.html?ct=32&op=92&item=98"
        #url = url.split("?")[1]
        print(request_line)
        url = request_line.split()[1] #Get URL with data
        url_data = url.split("?")[1] #Get data only (remove /config?)
        data = {x[0] : x[1] for x in [x.split("=") for x in url_data[0:].split("&") ]} #Create dict
        print(data)
        # z1 = data["_HR_ZONE_1"]
        # z2 = data["_HR_ZONE_2"]
        # z3 = data["_HR_ZONE_3"]
        # t = data["_HR_THRESHOLD"]
        config.save_config(data) # Save data to config
        file = open("success.html")
        html = file.read()
        file.close()
        writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        writer.write(html)

    elif request_line.find("/favicon") != -1:
        file = open("favicon.png", 'rb')
        favicon = file.read()
        file.close()
        writer.write(favicon)

    # Manual mode and manual speed settings
    elif request_line.find("/fan") != -1: # i.e. GET /fan/speed/3 HTTP/1.1
        url = request_line.split()[1] #Get URL i.e. /fan/speed/3
        if request_line.find("/manual_enable/true") != -1:
            relay_controller._MANUAL_MODE_ENABLED = True
        elif request_line.find("/manual_enable/false") != -1:
            # Set fan speed to 0 then turn manual mode off
            relay_controller.set_fan_speed(0, manualModeSetSpeed=True)
            relay_controller._MANUAL_MODE_ENABLED = False
        elif request_line.find("/fan/speed/") != -1:
            speed = int(url[-1])
            relay_controller.set_fan_speed(speed, manualModeSetSpeed=True)
        file = open("manual_mode.html")
        html = file.read()
        file.close()

        if relay_controller._MANUAL_MODE_ENABLED:
            html = html.replace('**_MANUAL_MODE_ENABLED**', 'checked')
            html = html.replace('**showSpeedButtons**', 'block')
        else:
            html = html.replace('**_MANUAL_MODE_ENABLED**', '')
            html = html.replace('**showSpeedButtons**', 'none')
        
        # Display current speed
        html = html.replace('**currentFanSpeed**', str(relay_controller.get_fan_speed()))
        
        writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        writer.write(html)


    elif request_line.find("/config") != -1: # i.e. GET /fan/speed/3 HTTP/1.1
        print("return config.html")
        file = open("config.html")
        html = file.read()
        file.close()

        html = html.replace('**hrZone1**', str(config._HR_ZONE_1))
        html = html.replace('**hrZone2**', str(config._HR_ZONE_2))
        html = html.replace('**hrZone3**', str(config._HR_ZONE_3))
        html = html.replace('**threshold**', str(config._HR_THRESHOLD))
        
        writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        writer.write(html)
    
    else:
        file = open("index.html")
        html = file.read()
        file.close()
        
        writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        writer.write(html)

    await writer.drain()
    await writer.wait_closed()
    print("Client disconnected")

async def main():
    print('Connecting to Network...')
    connect_to_network()

    print('Setting up webserver...')
    asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 80))
    while True:
        print("heartbeat")
        await asyncio.sleep(5)
        
try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()