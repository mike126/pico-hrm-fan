from machine import Pin,UART
import time

uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))
uart.init(bits=8, parity=None, stop=2)
led = Pin("LED", Pin.OUT)

# Send a sample HR reading ever 1 sec
while True:
    led.toggle() # Toggle on board LED for testing
    print("uart.any(): ", uart.any())
    if uart.any(): # Check any bytes in buffer
        # for i in (range(uart.any())):
        #     print(uart.read(1))
        line = uart.readline()
        if line is not None:
            _CURRENT_HR = line
            print("uart data received: ", line)
        # else:
        #     conccurent_none_hr_readings += 1
        #     if conccurent_none_hr_readings > 20 * (1/0.5): # If no readings from approx 20 sec set HR to None to stop transmitting over BLE
        #         _CURRENT_HR = None
    time.sleep_ms(200)
