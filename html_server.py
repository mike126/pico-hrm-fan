# TODO: Going to need to refactor this as it doesn't work async currently...
# Option 1: https://gist.github.com/aallan/3d45a062f26bc425b22a17ec9c81e3b6
# Option 2: https://github.com/belyalov/tinyweb try this second

import utime
import network
import asyncio
import socket
import ujson as json
# import urequests
from machine import Pin
import config


#open JSON file and load data if available
config.load_config()

ssid = '<SSID_here>'
password = '<wifi_password_here>'

async def connectWifiAndServeHTML():
    while True:
        wlan = network.WLAN(network.STA_IF) # set WiFi to station interface
        wlan.active(True) # activate the network interface
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
            await asyncio.sleep(1)

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


    # Open socket
    # addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    addr = (pico_ip, 80)
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # https://forum.micropython.org/viewtopic.php?t=10412
    # s.close() # Close socket incase already open
    # s = socket.socket() 
    s.bind(addr)
    s.listen(1)
    print('listening on', addr)

    # main loop
    while True:
        await asyncio.sleep(1) # Sleep so other func can run
        client, client_addr = s.accept()
        raw_request = client.recv(1024)
        # translate byte string to normal string variable
        raw_request = raw_request.decode("utf-8")

        print("############# NEW REQUEST RECEIVED #############")
        print(raw_request)

        # break request into words (split at spaces)
        request_parts = raw_request.split()
        http_method = request_parts[0]
        request_url = request_parts[1]

        # if request_url.find("/ledon") != -1:
            # turn LED on
            # led_state = True
            # led.on()
        # elif request_url.find("/ledoff") != -1:
            # turn LED off
            # led_state = False
            # led.off()

        # If config request
        if request_url.find("/config") != -1:
            #url = "http://www.example.org/default.html?ct=32&op=92&item=98"
            #url = url.split("?")[1]
            url = request_parts[-1]
            data = {x[0] : x[1] for x in [x.split("=") for x in url[0:].split("&") ]}
            print(data)
            # z1 = data["_HR_ZONE_1"]
            # z2 = data["_HR_ZONE_2"]
            # z3 = data["_HR_ZONE_3"]
            # t = data["_HR_THRESHOLD"]
            config.save_config(data)
            file = open("success.html")
            html = file.read()
            file.close()
            client.send(html)
            client.close()
        elif request_url.find("/favicon") != -1:
            file = open("favicon.png", 'rb')
            favicon = file.read()
            file.close()
            client.send(favicon)
            client.close()
        else:
            file = open("config.html")
            html = file.read()
            file.close()

            html = html.replace('**hrZone1**', str(config._HR_ZONE_1))
            html = html.replace('**hrZone2**', str(config._HR_ZONE_2))
            html = html.replace('**hrZone3**', str(config._HR_ZONE_3))
            html = html.replace('**threshold**', str(config._HR_THRESHOLD))
            client.send(html)
            client.close()

        # led_state_text = "OFF"
        # if led_state:
        #     led_state_text = "ON"

# asyncio.run(connectWifiAndServeHTML())