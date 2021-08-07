#!/usr/bin/python3

###########################
### dev tool Aug 2021
### get fresh copy of activity data with cursor
###########################

import requests
import json

###temp config
config = {
    'hotspot' : '112MWdscG3DjHTxdCrtuLkkXNSbxCkbqkuiu8X9zFDwsBfa2teCD',
    'owner' : '14hriz8pmxm51FGmk1nuijHz6ng9z9McfJZgsg4yxzF2H7No3mH',
    'cursor' : 'eyJtaW5fYmxvY2siOjg5NDEwOSwiYmxvY2siOjk1NTUwMCwiYW5jaG9yX2Jsb2NrIjo5NTU1MDB9',
    'api_endpoint' : 'https://api.helium.io/v1/'
}


###get activity data
activity_endpoint = config['api_endpoint'] +"hotspots/"+ config['hotspot'] +'/activity/?cursor='+ config['cursor']
#activity_endpoint = config['api_endpoint'] +"hotspots/"+ config['hotspot'] +'/activity/'
activity_request = requests.get(activity_endpoint)
data = activity_request.json()

###update data.json
with open("data.json", "w") as outfile:
        json.dump(data, outfile)

