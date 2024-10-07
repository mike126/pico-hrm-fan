import ujson as json

configFileName = 'config.json'

# Module global variables - to be read by relay_controller.py
global _HR_ZONE_1
global _HR_ZONE_2
global _HR_ZONE_3
global _HR_THRESHOLD

def setGlobals(data):
    global _HR_ZONE_1; _HR_ZONE_1 = int(data["_HR_ZONE_1"])
    global _HR_ZONE_2; _HR_ZONE_2 = int(data["_HR_ZONE_2"])
    global _HR_ZONE_3; _HR_ZONE_3 = int(data["_HR_ZONE_3"])
    global _HR_THRESHOLD; _HR_THRESHOLD = int(data["_HR_THRESHOLD"])

# Open JSON file and load data if available
def load_config():
    # Load JSON
    try:
        with open(configFileName, 'r') as f:
            data = json.load(f)
    # Default values if can't load
    except:
        print("Saved config not found, reverting to default values")
        data = {
            "_HR_ZONE_1": 110,
            "_HR_ZONE_2": 150,
            "_HR_ZONE_3": 170,
            "_HR_THRESHOLD": 7
        }
    # Set globals
    setGlobals(data)

# Save config to JSON file, pass data received from config.html POST
def save_config(data):
    # data = {
        # "_HR_ZONE_1": z1,
        # "_HR_ZONE_2": z2,
        # "_HR_ZONE_3": z3,
        # "_HR_THRESHOLD": t
    # }
    try:
        with open(configFileName, 'w') as f:
            json.dump(data, f)
            # Set globals
            setGlobals(data)
    except:
        print("Could not save config")
