import ujson as json

#open JSON file and load data if available
async def read():
    try:
        with open('config.json', 'r') as f:
            data = json.load(f)
            hr_z_1 = data["hrZone1"]
            hr_z_2 = data["hrZone2"]
            hr_z_3 = data["hrZone3"]
            print("Loaded saved JSON config: ", data)
    except:
        hr_z_1 = 110
        hr_z_2 = 150
        hr_z_3 = 170
        print("Saved config not found, reverting to default values")

# Save LED state to JSON file
def save_config():
    jsonData = {}
    jsonData["hrZone1"] = hr_z_1
    jsonData["hrZone2"] = hr_z_2
    jsonData["hrZone3"] = hr_z_3
    try:
        with open('config.json', 'w') as f:
            json.dump(jsonData, f)
    except:
        print("Could not save config")