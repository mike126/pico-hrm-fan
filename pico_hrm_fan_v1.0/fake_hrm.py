import sys

sys.path.append("")

from micropython import const

import uasyncio as asyncio
import aioble
import bluetooth

from machine import Pin,UART

###############################################
############# BLE HRM Details #################
_ENV_SENSE_UUID = bluetooth.UUID(0x180d) #Heart rate service UUID 
_ENV_SENSE_HEART_RATE_UUID  = bluetooth.UUID(0x2a37) #Heart rate characteristic
# org.bluetooth.characteristic.gap.appearance.xml
_ADV_APPEARANCE_GENERIC_HEART_RATE_SENSOR = const(832) #Generic heart rate sensor
_BLE_RETRANSMIT_DEVICE_NAME = "MICHAEL-HRM-H9"

# How frequently to send advertising beacons.
_ADV_INTERVAL_MS = 250_000
###############################################

# UART serial communication
_UART = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))
_UART.init(bits=8, parity=None, stop=2)
_LED = Pin("LED", Pin.OUT)

# Track current HR, set to None until reading received over UART
_CURRENT_HR = None


# Register GATT server.
hrm_service = aioble.Service(_ENV_SENSE_UUID)
hrm_characteristic = aioble.Characteristic(
    hrm_service, _ENV_SENSE_HEART_RATE_UUID, read=True, notify=True
)
aioble.register_services(hrm_service)

# Serially wait for connections. Don't advertise while a central is
# connected.
async def peripheral_task():
    global _CURRENT_HR

    while True:
        async with await aioble.advertise(
            _ADV_INTERVAL_MS,
            name=_BLE_RETRANSMIT_DEVICE_NAME,
            services=[_ENV_SENSE_UUID],
            appearance=_ADV_APPEARANCE_GENERIC_HEART_RATE_SENSOR,
        ) as connection:
            print("Connection from", connection.device)

            try:
                # Send current HR reading every 1 sec
                while True:
                    if _CURRENT_HR is not None:
                        hrm_characteristic.notify(connection, _CURRENT_HR)
                    await asyncio.sleep_ms(1000)
            # Catch exceptions, most likely disconnect. There's probably a better way to handle this
            except Exception as e:
                print("ERROR: ", e)
            # await connection.disconnected()

# Initialise UART and set up loop to read a line every 500ms (data should be transmitted every ~1s from other pi)
async def uart_init():
    _UART.read() # Read all bytes to clear buffer
    _UART.readline() # Readline to ensure not in the middle of a line

    global _CURRENT_HR # Global current HR value

    # Keep polling UART for HR readings, set when received
    # BLE will use this global to send HR reading
    conccurent_none_hr_readings = 0
    while True:
        if _UART.any(): # Check any bytes in buffer
            line = _UART.readline()
            if line is not None:
                _CURRENT_HR = line
                print("uart data received: ", line)
            else:
                conccurent_none_hr_readings += 1
                if conccurent_none_hr_readings > 20 * (1/0.5): # If no readings from approx 20 sec set HR to None to stop transmitting over BLE
                    _CURRENT_HR = None
        await asyncio.sleep_ms(500)

async def main():
    await asyncio.gather(uart_init(), peripheral_task())

asyncio.run(main())