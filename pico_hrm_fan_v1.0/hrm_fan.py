import sys

sys.path.append("")

from micropython import const

import relay_controller

import uasyncio as asyncio
import aioble
import bluetooth
import utime

from machine import Pin,UART

# Track last HR reading time
_LAST_READING_TIME = utime.ticks_ms()
# Time to wait after last reading before turning fan off (milliseconds)
_WAIT_MS_TO_TURN_FAN_OFF = 30 * 1000 # 30 sec

# TODO: Use struct to decode HR data 'properly'
# import struct

# Define UUID for BLE service and characteristic
_BLE_UUID_HEART_RATE_SERVICE = bluetooth.UUID(0x180d) #Heart rate service UUID 
_BLE_UUID_HEART_RATE_MEASUREMENT_CHAR  = bluetooth.UUID(0x2a37) #Heart rate characteristic
_BLE_DEVICE_NAME = "Polar H9 BC6BA927"

# UART Serial Data Transmission. Used to transmit HR readings to second pico w acting as a 'fake hrm'
# Need to do this to allow other devices to get BLE HRM readings as Polar H9 only supports one BLE connection
_UART = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))
_UART.init(bits=8, parity=None, stop=2)

#Alternative service/chars for Polar/Kickr
#_ENV_SENSE_UUID = bluetooth.UUID(0x1818)  #KICKR CORE SERVICE
#_CHAR_UUID = bluetooth.UUID(0x2A65) KICKR something or other
#_CHAR_UUID = bluetooth.UUID(0x2A38) #BODY SENSOR LOCATION 
# https://github.com/sputnikdev/bluetooth-gatt-parser/blob/master/src/main/resources/gatt/characteristic/org.bluetooth.characteristic.body_sensor_location.xml

# Helper to decode the HRM value
def _decode_hrm(data):
    # Below decodes a temp value - probably the proper way to do
    #return struct.unpack("<h", data)[0] / 100

    # NEW PROCESSING (WORK IN PROGRESS) https://stackoverflow.com/questions/67024800/ble-heart-rate-senser-value-interpretation
    # Bits are numbered from LSB (0) to MSB (7).
    # Bit 0 - Heart Rate Value Format: 0 => UINT8 beats per minute, 1 => UINT16 BPM
    # Bit 1-2 - Sensor Contact Status: 00 => Not supported or detected, others ??
    # Bit 3 - Energy Expended Status: 0 => No Present, others ??
    # Bit 4 - RR-Interval: 1 => One or more values are present, others ??
    
    # Check first bit is 0 => UINT8 BPM, i.e. Byte index 1 contain 0-255 bpm readings range 
    if testBit(list(data)[0], 0) == 0: 
        # Second byte (index 1) contains BPM, just return this value
        return list(data)[1]
    else:
        return 0 # Should actually decode 2nd and 3rd bytes (index 1-2) as a uint16 value, but for now assume something gone wrong and report 0

# Check value of a bit at position offset. Returns 0 if bit is 0, returns bits value if 1 (2^offset)
# i.e. 5 = 101 will return 4 for inputs (5,2), 0 for (5,1) and 1 for (5,0)
# https://wiki.python.org/moin/BitManipulation
def testBit(int_type, offset):
    mask = 1 << offset
    return(int_type & mask)

async def find_hr_sensor():
    # Scan for 5 seconds, in active mode, with very low interval/window (to
    # maximise detection rate).
    async with aioble.scan(5000, interval_us=30000, window_us=30000, active=True) as scanner:
        async for result in scanner:
            # Print list of all services for each BLE device found (for debugging)
            #print(result, result.name(), result.rssi, result.services())
            #for i in result.services():
            #    print(i)
            #if result.name() == "KICKR CORE 5A52" and _BLE_UUID_HEART_RATE_SERVICE in result.services():
            # Check if matches device name and the heart rate service UUID.
            if result.name() == _BLE_DEVICE_NAME and _BLE_UUID_HEART_RATE_SERVICE in result.services():    
                return result.device
    return None

async def main():
    # Find HR sensor, then attempt to connect if found
    device = await find_hr_sensor()
    if not device:
        print("Polar H9 HRM not found")
        return

    try:
        print("Connecting to", device)
        connection = await device.connect()
    except asyncio.TimeoutError:
        print("Timeout during connection")
        return
    except Exception as e:
        print("Error during connection: ", e)
        return

    # If device connection succeeded, attempt to connect to HR service and sub to characteristic
    async with connection:
        try: 
            heart_rate_service = await connection.service(_BLE_UUID_HEART_RATE_SERVICE)
            # List characteristics for service (debug purposes)
            #print("listing characteristics for service ", heart_rate_service,":")
            #async for c in heart_rate_service.characteristics():
            #    print(c)
            heart_rate_characteristic = await heart_rate_service.characteristic(_BLE_UUID_HEART_RATE_MEASUREMENT_CHAR )
        except asyncio.TimeoutError:
            print("Timeout discovering services/characteristics")
            return
        except Exception as e:
            print("Characteristic await error: ", e)
            return

        try:
            print("Subscribing to heart rate characteristic")
            print(heart_rate_characteristic)
            await heart_rate_characteristic.subscribe(notify=True)
        except Exception as e:
            print("Subscribe failed: ", e)

        while True:
            try:
                raw_hr_reading_data = await heart_rate_characteristic.notified()
                hr = _decode_hrm(raw_hr_reading_data)
                print(hr, "bpm, raw: ", raw_hr_reading_data)
                # Transmit raw reading over UART Tx pin for second BLE pico
                _UART.write(raw_hr_reading_data)

                # Set new latest reading time
                _LAST_READING_TIME = utime.ticks_ms()
                # print("new last time set: ", _LAST_READING_TIME)

                # Set fan speed from HR reading
                relay_controller.calculate_and_set_fan_speed_from_hr(hr)

                # Wait 1 sec
                await asyncio.sleep_ms(1000)
            except Exception as e:
                print("Error: ", e)
                print("Attempting to reconnect...")
                return

# Loop main function, will attempt to reconnect upon disconnection
async def loop_main():
    while True:
        await main()

        # Before running main again, if more than 30s passed since last reading, turn off fan 
        if (relay_controller.get_fan_speed() != 0 and
            utime.ticks_diff(utime.ticks_ms(), _LAST_READING_TIME) >= _WAIT_MS_TO_TURN_FAN_OFF ): 
            print("Timeout, set fan to 0")
            relay_controller.set_fan_speed(0)

print("Initial reading time:", _LAST_READING_TIME)
relay_controller.set_fan_speed(0)
asyncio.run(loop_main())
