
import json
from time import time
from datetime import datetime

config = {}

def niceDate(time):
    timestamp = datetime.fromtimestamp(time)
    return timestamp.strftime("%H:%M %d/%b").upper()

###load config.json vars
def loadConfig():
    global config
    with open('config.json') as json_data_file:
        config = json.load(json_data_file)

loadConfig()

#nice dates
config['last']['send_nice'] = niceDate(config['last']['send'])
config['next']['report_nice'] = niceDate(config['next']['report'])

print(json.dumps(config, indent=2))