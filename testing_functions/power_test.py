from machine import Pin
import utime

led = Pin("LED", Pin.OUT)

# Blink led 2x/sec, use to test power source is working. 
while True:
    led.value(1) # led on. Note: led.on() also works
    utime.sleep_ms(250)
    led.value(0) # led off. Note: led.off() also works
    utime.sleep_ms(250)
