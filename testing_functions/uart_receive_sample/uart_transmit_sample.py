from machine import Pin,UART
import time

uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))
uart.init(bits=8, parity=None, stop=2)
led = Pin("LED", Pin.OUT)

# Send a sample HR reading ever 1 sec
while True:
    uart.write(b'\x10]\xae\x02') #93 bpm
    # uart.write(b'\n') #new line
    led.toggle() 
    time.sleep(1)

    uart.write(b'\x10^y\x02A\x02') #94 bpm
    # uart.write(b'\n') #new line
    led.toggle() 
    time.sleep(1)

    uart.write(b'\x10_j\x02') #95 bpm
    # uart.write(b'\n') #new line
    led.toggle() 
    time.sleep(1)

    uart.write(b'\x10au\x02g\x02') #97 bpm
    # uart.write(b'\n') #new line
    led.toggle() 
    time.sleep(1)

    uart.write(b'\x10bY\x02B\x02') #98 bpm
    # uart.write(b'\n') #new line
    led.toggle() 
    time.sleep(1)