import sys

sys.path.append("")

from micropython import const

import relay_controller

import uasyncio as asyncio
import aioble
import bluetooth
import utime

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

# Current HR for fake HRM
_CURRENT_HR_READING_RAW = b'\x00\x00' #Set to 0 bpm initially


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
        print("ERROR connecting to device ", e)
        return


    # If device connection succeeded, attempt to connect to HR service and sub to characteristic
    async with connection:
        try: 
            heart_rate_service = await connection.service(_BLE_UUID_HEART_RATE_SERVICE)
            heart_rate_characteristic = await heart_rate_service.characteristic(_BLE_UUID_HEART_RATE_MEASUREMENT_CHAR )
        except asyncio.TimeoutError:
            print("Timeout discovering services/characteristics")
            return
        except Exception as e:
            print("ERROR discovering services/characteristics", e)

        try:
            print("Subscribing to heart rate characteristic")
            print(heart_rate_characteristic)
            await heart_rate_characteristic.subscribe(notify=True)
        except Exception as e:
            print("Subscribe failed: ", e)

        while True:
            try:
                raw_hr_reading_data = await heart_rate_characteristic.notified()
                # Set global HR reading for fake HRM
                _CURRENT_HR_READING_RAW = raw_hr_reading_data             
                print("raw: ", raw_hr_reading_data)

                # Wait 1 sec
                await asyncio.sleep_ms(1000)
            except Exception as e:
                print("Error: ", e)
                print("Attempting to reconnect...")
                return

# Loop main function, will attempt to reconnect upon disconnection
async def loop_main():
    while True:
        await asyncio.sleep_ms(12000)
        await main()

        # Before running main again, if more than 30s passed since last reading, turn off fan 
        if (relay_controller.get_fan_speed() != 0 and
            utime.ticks_diff(utime.ticks_ms(), _LAST_READING_TIME) >= _WAIT_MS_TO_TURN_FAN_OFF ): 
            print("Timeout, set fan to 0")
            relay_controller.set_fan_speed(0)

print("Initial reading time:", _LAST_READING_TIME)


################################################################
################################################################
################################################################
### FAKE HRM CODE
_ENV_SENSE_UUID = bluetooth.UUID(0x180d) #Heart rate service UUID 
_ENV_SENSE_HEART_RATE_UUID  = bluetooth.UUID(0x2a37) #Heart rate characteristic
# org.bluetooth.characteristic.gap.appearance.xml
_ADV_APPEARANCE_GENERIC_HEART_RATE_SENSOR = const(832) #Generic heart rate sensor
_BLE_RETRANSMIT_DEVICE_NAME = "MICHAEL-HRM-H9"

# How frequently to send advertising beacons.
_ADV_INTERVAL_MS = 250_000


# Register GATT server.
hrm_service = aioble.Service(_ENV_SENSE_UUID)
hrm_characteristic = aioble.Characteristic(
    hrm_service, _ENV_SENSE_HEART_RATE_UUID, read=False, notify=True
)
aioble.register_services(hrm_service)

# Serially wait for connections. Don't advertise while a central is
# connected.
async def fake_hrm_peripheral_task():
    print("STARTING FAKE HRM PERIPHERAL TASK!!!!!!!!!!!!!!!!!!!!!!!!!")
    while True:
        async with await aioble.advertise(
            _ADV_INTERVAL_MS,
            name=_BLE_RETRANSMIT_DEVICE_NAME,
            services=[_ENV_SENSE_UUID],
            appearance=_ADV_APPEARANCE_GENERIC_HEART_RATE_SENSOR,
        ) as connection:
            print("Connection from", connection.device)
            # for i in range (120):
            while True:
                hrm_characteristic.notify(connection, _CURRENT_HR_READING_RAW)
                await asyncio.sleep_ms(1000) # Wait 1 sec between notifications

                # Sample data for testing without actual HRM data
                hrm_characteristic.notify(connection, b'\x10]\xae\x02')
                await asyncio.sleep_ms(1000)
                hrm_characteristic.notify(connection, b'\x10^y\x02A\x02')
                await asyncio.sleep_ms(1000)
                hrm_characteristic.notify(connection, b'\x10_j\x02')
                await asyncio.sleep_ms(1000)
                hrm_characteristic.notify(connection, b'\x10au\x02g\x02')
                await asyncio.sleep_ms(1000)
                hrm_characteristic.notify(connection, b'\x10bY\x02B\x02')
                await asyncio.sleep_ms(1000)
            await connection.disconnected()

# asyncio.run(peripheral_task())
################################################################
################################################################
################################################################



# Run both tasks.
async def test_main():
    t1 = asyncio.create_task(loop_main())
    t2 = asyncio.create_task(fake_hrm_peripheral_task())
    await asyncio.gather(t1, t2)


asyncio.run(test_main())

