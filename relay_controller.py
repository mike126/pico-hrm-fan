from machine import Pin
import config

# Define relay output pins
_FAN_SPEED_1_PIN = Pin(18, mode=Pin.OUT)
_FAN_SPEED_2_PIN = Pin(19, mode=Pin.OUT)
_FAN_SPEED_3_PIN = Pin(20, mode=Pin.OUT)

# Track current fan speed
_CURRENT_FAN_SPEED = 0

# Define on/off value for relay
# (depends if relay is active high or active low)
_RELAY_OFF = 1
_RELAY_ON = 0

# Manual mode (overrides HR control when enabled via http request)
global _MANUAL_MODE_ENABLED
_MANUAL_MODE_ENABLED = False

# Load config incl heart rate zones and threshold (relate to fan speeds). 
# Threshold HR to move back down a zone. This is to prevent fan speed
# toggling constantly when sitting on the edge of a HR zone
config.load_config()

# Set fan speed, values 0 = off, 1-3 = fan speeds
# Called after calculating speed to be set based on HR
# _CURRENT_FAN_SPEED updated on each successful speed change
def set_fan_speed(speed, manualModeSetSpeed = False):
    global _MANUAL_MODE_ENABLED

    # Ignore speeds set from HR when in manual mode and vice versa
    # I.e. only allow manual speeds set in manual mode, and HR speeds set 
    # when not in manual mode
    if _MANUAL_MODE_ENABLED and not manualModeSetSpeed: return
    elif not _MANUAL_MODE_ENABLED and manualModeSetSpeed: return

    global _CURRENT_FAN_SPEED

    # Don't do anything if no change in speed
    if speed == _CURRENT_FAN_SPEED and speed > 0: return

    # Turn all relays off
    _FAN_SPEED_1_PIN.value(_RELAY_OFF)
    _FAN_SPEED_2_PIN.value(_RELAY_OFF)
    _FAN_SPEED_3_PIN.value(_RELAY_OFF)

    # Turn on corresponding pin if speed 1, 2 or 3
    if speed == 0:
        _CURRENT_FAN_SPEED = 0
    elif speed == 1:
        _FAN_SPEED_1_PIN.value(_RELAY_ON)
        _CURRENT_FAN_SPEED = 1
    elif speed == 2:
        _FAN_SPEED_2_PIN.value(_RELAY_ON)
        _CURRENT_FAN_SPEED = 2
    elif speed == 3:
        _FAN_SPEED_3_PIN.value(_RELAY_ON)
        _CURRENT_FAN_SPEED = 3
    else:
        print("ERROR: Unknown speed")
    
    print("Fan speed set to: ", _CURRENT_FAN_SPEED)

    return

def calculate_and_set_fan_speed_from_hr(heart_rate):
    # Sanity check: return if data unrealistic
    # Most likely case HR=0 if disconnected
    if heart_rate > 210 or heart_rate <= 30: 
        return
     
    # If HR less than zone 1
    elif heart_rate < config._HR_ZONE_1:
        # If fan running, set speed to 0 when HR dips more than _HR_THRESHOLD below zone 1
        if _CURRENT_FAN_SPEED >= 1 and heart_rate < (config._HR_ZONE_1 - config._HR_THRESHOLD):
            set_fan_speed(0)
        # Else if fan already speed 0 do nothing
        else: return

    # If HR in zone 1 and less than zone 2
    elif heart_rate < config._HR_ZONE_2:
        # If fan off, set to speed 1 
        if _CURRENT_FAN_SPEED == 0:
            set_fan_speed(1)
        # If fan already at speed 1, do nothing
        elif _CURRENT_FAN_SPEED == 1:
            return
        # If fan above speed 1, move down to speed 1 when HR dips more than _HR_THRESHOLD below zone 2
        elif _CURRENT_FAN_SPEED >= 2 and heart_rate < (config._HR_ZONE_2 - config._HR_THRESHOLD):
            set_fan_speed(1)

    # If HR in zone 2 and less than zone 3
    elif heart_rate < config._HR_ZONE_3: 
        # If fan speed < 2 set to 2:
        if _CURRENT_FAN_SPEED == 1:
            set_fan_speed(2)
        # If fan already at speed 2, do nothing
        elif _CURRENT_FAN_SPEED == 2:
            return
        # If fan above speed 2, move down to speed 2 when HR dips more than _HR_THRESHOLD below zone 3
        elif _CURRENT_FAN_SPEED >= 3 and heart_rate < (config._HR_ZONE_3 - config._HR_THRESHOLD):
            set_fan_speed(2)

    # If HR in zone 3
    elif heart_rate >= config._HR_ZONE_3: 
        # Set fan speed to 3
        if _CURRENT_FAN_SPEED != 3: 
            set_fan_speed(3)
            
    return  

def get_fan_speed():
    return _CURRENT_FAN_SPEED

# Set speed to 0 initially (shouldn't be needed, but for safety)
print("SETTING INITIAL SPEED: ", _CURRENT_FAN_SPEED)
set_fan_speed(0)
config.load_config()