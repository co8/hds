#!/usr/bin/python3

############################
# 07/04/21 JULY
# co8.com
# HDS
# Helium Hotspot Discord Status
############################

####import libs
from time import time
import requests
import json
from datetime import datetime
from discord_webhook import DiscordWebhook

###load config.json vars
with open("config.json") as json_data_file:
    config = json.load(json_data_file)

###dictionary
hs = {} #main
new_activity = send_discord = welcome = False

###vars
check_interval_minutes = 10
check_interval = check_interval_minutes*60*60
status_interval_minutes = 60
status_interval = status_interval_minutes*60*60
niceNum = .00000001
activity_data = ''
activity_cursor = ''
discord_content = ''
api_endpoint = 'https://api.helium.io/v1/'

###functions
def NiceName(name):
    return name.replace('-', ' ').title().upper()

def NameInitials(name):
    nicename = NiceName(name)
    return "".join(item[0].upper() for item in nicename.split())

def NiceBalance(balance):
    intbal = int(balance)
    bal = str(round(intbal*niceNum, 2))
    return str(bal) +" 🌮"

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
    #'activity_last_time' : 0,
    'rewards' : []
}
hs['rewards'] = {'amount_nice': NiceBalance(0)}
del hotspot_request, hotspot_response

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
del wallet_request, w

#### New User Welcome
if 'activity_last_time' not in config:
    print('Adding Welcome msg')
    send_discord = welcome = True
    discord_content += '🤙 '+ hs['name'] +' ('+ hs['initials'] +') 📡\n'

    
###activity data
activity_endpoint = api_endpoint +"hotspots/"+ config['hotspot'] +'/activity/'
#get fresh activity
activity_request = requests.get(activity_endpoint)
activity = activity_request.json() 
del activity_request


if bool(activity['data']):
    #if data in first request, use that new data
    print('have fresh activity data')
    activity_data = activity['data'][0]
    send_discord = True
else:
    #get activity using cursor
    print('getting activity with cursor') 
    config['activity_cursor'] = activity['cursor']
    activity_cursor_request = requests.get(activity_endpoint +'?cursor='+ config['activity_cursor'])
    activity = activity_cursor_request.json()
    activity_data = activity['data'][0]
    #add activity_cursor and write to config.json
    print('writing activity cursor to config')
    UpdateConfig(config)
    del activity_cursor_request
del activity

#######################################################
### check for new activity 
#get hs.last_time from activity_data
hs['activity_last_time'] = activity_data['time']
#check for config.last_time
if 'activity_last_time' not in config:
    config['activity_last_time'] = 0
#######################################################

#get rewards for activity if exists
if 'rewards' in activity_data:
    print('YES rewards in actvity')
    hs_rewards = activity_data['rewards'][0]
    hs_rewards['time'] = activity_data['time']
    hs_rewards['amount_nice'] = NiceBalance(hs_rewards['amount'])
    hs['rewards'] = hs_rewards # add into hs
    del hs_rewards
else:
    print('no rewards in actvity')

#compare config.last_time to hs.last_time
if config['activity_last_time'] == hs['activity_last_time']:
    #new_activity = False
    print('last_times are equal. no new activity')
else:
    print('New Activity. last_times are NOT equal')
    new_activity = True
    #set last_time in config
    config['activity_last_time'] = hs['activity_last_time'] = activity_data['time']
    config['activity_last_type'] = hs['activity_last_type'] = activity_data['type']
    #write to config
    print('writing new activity last_type and last_time to config')
    UpdateConfig(config)

###get timestamp NOW
now = datetime.now()
hs['now'] = round(datetime.timestamp(now))
hs['time'] = now.strftime("%D %H:%M")
del now

#######################################################
### Send Status if no new activity, but >60min since last msg sent
####
# time since last sent?
minutes = 0
if 'status_last_sent' in config:
    total_seconds = (hs['now'] - config['status_last_sent'])
    minutes = round(total_seconds/60)
    #exit()
else:
    config['status_last_sent'] = hs['now']

if minutes >= 60:
    send_discord = True
print('Time since last status: '+ str(minutes))
#######################################################

###discord - create content msg
#default msg
discord_content += '📡 '+ hs['initials'] +' Status: '+ hs['status'] +' / Height: '+ hs['height_percentage'] +' / Scale: '+ hs['reward_scale'] +'\n💰 Wallet: '+ hs['balance'] +'\n'

#new msg if new activity
if bool(new_activity):
    print('adding new activity msg')
    activity_time = datetime.fromtimestamp(hs['activity_last_time']).strftime("%H:%M %m/%d")
    #for first status msg
    if bool(welcome):
        discord_content += 'Last '
    else:
        discord_content += '🚀 '
    discord_content += hs['initials'] +' Activity: '+ str(config['activity_last_type']).upper() +' ('+ hs['rewards']['amount_nice'] +') '+ activity_time

print('welcome: '+ str(welcome))
print('new_activity: '+ str(new_activity))
print('send discord: '+ str(send_discord))
#print(discord_content)
#print(config)
#exit()

testSend = True

###discord send###
if bool(send_discord) and bool(testSend):
    if bool(testSend):
        discord_content = 'welcome: '+ str(welcome) +'new_activity: '+ str(new_activity) +'send discord: '+ str(send_discord)
    webhook = DiscordWebhook(url=config['discord_webhook'], content=discord_content)
    webhook_response = webhook.execute()
    print(webhook_response)
    del webhook, webhook_response

### clean up
UpdateConfig(config)
del hs,config 