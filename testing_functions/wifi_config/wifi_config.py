# use web interface to control an LED

import utime
import network
import socket
# import urequests
from machine import Pin

ssid = '<SSID_here>'
password = '<wifi_password_here>'

# set WiFi to station interface
wlan = network.WLAN(network.STA_IF)
# activate the network interface
wlan.active(True)
# connect to wifi network
wlan.connect(ssid, password)

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
    utime.sleep(1)

# check connection
if wlan.status() != 3:
    # No connection
    raise RuntimeError('network connection failed')
else:
    # connection successful
    print('wlan connected')
    status = wlan.ifconfig()
    pico_ip = status[0]
    print('ip = ' + status[0])

# Open socket
# addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
addr = (pico_ip, 80)
s = socket.socket()
s.bind(addr)
s.listen(1)
print('listening on', addr)

led = Pin("LED", Pin.OUT)
led.off()
led_state = False

# main loop
while True:
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

    if request_url.find("/ledon") != -1:
        # turn LED on
        led_state = True
        led.on()
    elif request_url.find("/ledoff") != -1:
        # turn LED off
        led_state = False
        led.off()

    # If config request
    elif request_url.find("/config") != -1:
        #url = "http://www.example.org/default.html?ct=32&op=92&item=98"
        #url = url.split("?")[1]
        url = request_parts[-1]
        dict = {x[0] : x[1] for x in [x.split("=") for x in url[1:].split("&") ]}
        hr_z_1 = dict["name"]
        hr_z_2 = dict["lname"]
        print(dict)

    else:
        # do nothing
        pass

    led_state_text = "OFF"
    if led_state:
        led_state_text = "ON"

    file = open("config.html")
    html = file.read()
    file.close()

    html = html.replace('**ledState**', led_state_text)
    html = html.replace('**hrZone1**', "123")    
    html = html.replace('**hrZone2**', "456")    
    html = html.replace('**hrZone3**', "789")    
    html = html.replace('**threshold**', "7")    
    client.send(html)
    client.close()