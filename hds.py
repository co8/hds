#!/usr/bin/python3

############################
# 07/04/21 JULY
# co8.com
# HDS
# Helium Hotspot Discord Status
############################

####import libs
import requests
import json
from datetime import datetime
from discord_webhook import DiscordWebhook

###load config.json vars
with open("config.json") as json_data_file:
    config = json.load(json_data_file)

###dictionary
hs = {} #main
new_activity = False

###vars
niceNum = .00000001
activity_cursor = ''
discord_content = ''
api_endpoint = 'https://api.helium.io/v1/'

###functions
def NiceName(name):
    return name.replace('-', ' ').title()

def NameInitials(name):
    nicename = NiceName(name)
    return "".join(item[0].upper() for item in nicename.split())

def NiceBalance(balance):
    intbal = int(balance)
    bal = str(round(intbal*niceNum, 2))
    return str(bal)+" HNT"

def UpdateConfig(config):
    with open("config.json", "w") as outfile:
        json.dump(config, outfile)



###hotspot data
hotspot_request = requests.get(api_endpoint +"hotspots/"+ config['hotspot'])
hotspot_response = hotspot_request.json()
hs = {
    'owner' : hotspot_response['data']['owner'],
    'name' : NiceName(hotspot_response['data']['name']),
    'status' : str(hotspot_response['data']['status']['online']).upper(),
    'height' : hotspot_response['data']['status']['height'],
    'block' : hotspot_response['data']['block'],
    'reward_scale' : str(round(hotspot_response['data']['reward_scale'],2)),
    #'last_time' : 0,
    'rewards' : []
}
hs['rewards'] = {'amount_nice': NiceBalance(0)}

###add owner to config
if 'owner' not in config:
    config['owner'] = hs['owner']
    UpdateConfig(config)

hs['initials'] = NameInitials(hs['name'])
hs['height_percentage'] = str(round(hs['height'] / hs['block'] * 100, 3)) +'%'

###wallet data
wallet_request = requests.get(api_endpoint +"accounts/"+ hs['owner'])
w = wallet_request.json()
hs['balance'] = NiceBalance(w['data']['balance'])

#### New User Welcome
if 'last_time' not in config:
    print('Adding Welcome msg')
    discord_content += '🤙 Status for '+ hs['name'] +' aka '+ hs['initials'] +'\n'

    
###activity data
activity_endpoint = api_endpoint +"hotspots/"+ config['hotspot'] +'/activity/'
#get fresh activity
activity_cursor_request = requests.get(activity_endpoint)
activity = activity_cursor_request.json() 

if bool(activity['data']):
    print('have fresh activity data')
    activity_data = activity['data']
else:
    #get activity using cursor
    print('getting activity with cursor') 
    config['activity_cursor'] = activity['cursor']
    activity_request = requests.get(activity_endpoint +'?cursor='+ config['activity_cursor'])
    activity = activity_request.json()
    activity_data = activity['data']
    #add activity_cursor and write to config.json
    print('writing activity cursor to config')
    UpdateConfig(config)

### check for new activity 
#get hs.last_time from activity_data
hs['last_time'] = activity['data'][0]['time']
#check for config.last_time
if 'last_time' not in config:
    config['last_time'] = 0


#get rewards for activity if exists
if 'rewards' in activity['data'][0]:
    print('YES rewards in actvity')
    hs_rewards = activity['data'][0]['rewards'][0]
    hs_rewards['time'] = activity['data'][0]['time']
    hs_rewards['amount_nice'] = NiceBalance(activity['data'][0]['rewards'][0]['amount'])
    hs['rewards'] = hs_rewards
else:
    print('no rewards in actvity')

#compare config.last_time to hs.last_time
#print(config['last_time'], type(config['last_time']), hs['last_time'], type(hs['last_time']))
#exit()
if config['last_time'] == hs['last_time']:
    #new_activity = False
    print('last_times are equal. no new activity')
else:
    print('New Activity. last_times are NOT equal')
    new_activity = True
    #set last_time in config
    config['last_time'] = hs['last_time'] = activity_data[0]['time']
    config['last_type'] = hs['last_type'] = activity_data[0]['type']
    #write to config
    print('writing new activity last_type and last_time to config')
    UpdateConfig(config)

###get timestamp NOW
now = datetime.now()
current_time = now.strftime("%D %H:%M")
hs['time'] = current_time

###discord - create content msg
#default msg
discord_content += '📡 '+ hs['initials'] +' Status: '+ hs['status'] +' / Height: '+ hs['height_percentage'] +' / Scale: '+ hs['reward_scale'] +'\n💰 Wallet: '+ hs['balance'] +'\n'

#new msg if new activity
if bool(new_activity):
    print('adding new activity msg')
    activity_time = str(datetime.fromtimestamp(hs['last_time']))
    discord_content += '🚀 '+ hs['initials'] +' Activity: '+ str(config['last_type']).upper() +' ('+ hs['rewards']['amount_nice'] +') '+ activity_time


print(discord_content)
#print(hs)
exit()

###discord send###
webhook = DiscordWebhook(url=config['discord_webhook'], content=discord_content)
webhook_response = webhook.execute()
print(webhook_response)
hs = {} #main