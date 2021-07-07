#!/usr/bin/python3

############################
# 07/04/21 JULY
# co8.com 
# enrique r grullon
# e@co8.com
# discord: co8#1934 
# HDS
# Helium Hotspot Discord Status
############################

########
# crontab -e
# check every 5 minutes. log to file
# */5 * * * * cd ~/hds; python3 hds.py  >> ~/cron.log 2>&1
#
# @reboot cd ~/hds; python3 hds.py  >> ~/cron.log 2>&1 
# - run at reboot for dedicated device, eg: RasPi Zero W
###
# install DiscordWebhook module
# % pip3 install discord-webhook
########

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
new_activity = send_discord = welcome = new_balance = False

###vars
status_interval_minutes = 58
niceNum = .00000001
activity_data = ''
activity_cursor = ''
discord_content = ''
api_endpoint = 'https://api.helium.io/v1/'

###functions
def NiceName(name):
    return name.replace('-', ' ').upper()

def NameInitials(name):
    nicename = NiceName(name)
    return "".join(item[0].upper() for item in nicename.split())

def NiceBalance(balance):
    intbal = int(balance)
    bal = '{:.2f}'.format(round(intbal*niceNum, 2))
    return str(bal)

def UpdateConfig(config):
    with open("config.json", "w") as outfile:
        json.dump(config, outfile)

### Activity Short Names
typeShortNames = {
    'poc_receipts_v1' : 'PoC B||W',
    'poc_receipts_v2' : 'PoC B||W',
    'poc_request_v1' : 'PoC CHALLENGER',
    'poc_request_v2' : 'PoC CHALLENGER',
    'rewards_v1' : 'REWARD',
    'rewards_v2' : 'REWARD',
    'state_channel_close_v1' : 'PACKETS',
    'state_channel_close_v2' : 'PACKETS'
}
def ActivityShortName(type):
    if type in typeShortNames:
        output = typeShortNames[type]
    else:
        output = type.upper()
    return output



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
hs['rewards'] = {
    'new_balance' : new_balance,
    'amount_nice': NiceBalance(0)
    }
del hotspot_request, hotspot_response

### get NOW
now = datetime.now()
hs['now'] = round(datetime.timestamp(now))
hs['time'] = str(now.strftime("%D %H:%M"))
del now

hs['initials'] = NameInitials(hs['name'])
hs['height_percentage'] = str(round(hs['height'] / hs['block'] * 100, 3)) +'%'

###add owner to config
if 'owner' not in config:
    config['owner'] = hs['owner']
    
###wallet data
wallet_request = requests.get(api_endpoint +"accounts/"+ config['owner'])
w = wallet_request.json()
hs['balance'] = NiceBalance(w['data']['balance'])
if 'balance_last' not in config:
    config['balance_last'] = '0'
###add to config if new
if hs['balance'] > config['balance_last']:
    new_balance = True
    print('config.balance_last: '+ str(config['balance_last']) +'\nhs.balance: '+ str(hs['balance']) +'\nnew_balance: '+ str(new_balance))
    config['balance_last'] = hs['balance']
    UpdateConfig(config)
del wallet_request, w

#### New User Welcome
if 'status_last_sent' not in config:
    print('Adding Welcome msg')
    send_discord = welcome = True
    discord_content += '🤙 **'+ hs['name'] +'   [ '+ hs['initials'] +' ]**  🤘\n'

    
###activity data
activity_endpoint = api_endpoint +"hotspots/"+ config['hotspot'] +'/activity/'
#get fresh activity
activity_request = requests.get(activity_endpoint)
activity = activity_request.json() 
del activity_request

#######################################################
### Send Status if no new activity, but >60min since last msg sent
####
# time since last sent?
minutes = 0
if 'status_last_sent' in config:
    total_seconds = (hs['now'] - config['status_last_sent'])
    minutes = round(total_seconds/60)
if minutes >= status_interval_minutes:
    send_discord = True
    print('send_discord = True. minutes >= status_interval_minutes')
    
print('last status: '+ str(minutes) +'min ago')
#######################################################

if bool(activity['data']):
    #if data in first request, use that new data
    print('have fresh activity data')
    activity_data = activity['data'][0]
    send_discord = True
elif send_discord == False and 'status_last_sent' in config: 
    # quit and done until next check. 
    # don't get activity if sent activity and no new data
    print(hs['time'] +' Nothing new. Quietly Quiting. Will try again Later 🤙')
    quit()
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
    new_activity = send_discord = False
    print('last_times are equal. no new activity')
else:
    print('New Activity. activity_last_times are NOT equal')
    new_activity = send_discord = True
    #set last_time in config
    config['activity_last_time'] = hs['activity_last_time'] = activity_data['time']
    config['activity_last_type'] = hs['activity_last_type'] = activity_data['type']
    #write to config
    print('writing new activity last_type and last_time to config')
    UpdateConfig(config)


###discord - create content msg
### bold balance has increased
balance_style = hs['balance']
if bool(new_balance):
    balance_style = '🧨**'+ hs['balance'] +'**'

#default msg
discord_content += '📡 '+ hs['initials'] +'  🔥  **'+ hs['status'] +'**   📦  '+ hs['height_percentage'] +'   🍕  '+ hs['reward_scale'] +'   🥓  '+ balance_style

if bool(new_activity):
    send_discord = True
    print('adding new activity msg')
    activity_time = datetime.fromtimestamp(hs['activity_last_time']).strftime("%H:%M %b.%d").upper()
    #for first status msg
    discord_content += '\n'
    if bool(welcome):
        discord_content += 'Last '
    else:
        discord_content += '🚀 '

    shortname = ActivityShortName(str(config['activity_last_type']))
    if_reward = ''
    #print(hs['rewards'])
    #exit()
    if 'rewards' in hs:
        if_reward = ' 🥓'+ hs['rewards']['amount_nice']
    discord_content += hs['initials'] +' Activity: **'+ shortname + if_reward +'**   '+ activity_time
    #discord_content += hs['initials'] +' Activity: **'+ shortname +' 🥓'+ hs['rewards']['amount_nice'] +'**   '+ activity_time
    #discord_content += hs['initials'] +' Activity: **'+ str(config['activity_last_type']).upper() +' 🥓'+ hs['rewards']['amount_nice'] +'**   '+ activity_time

#######################################################
### Send Status if no new activity, but >60min since last msg sent
####
# time since last sent?
minutes = 0
if 'status_last_sent' in config:
    total_seconds = (hs['now'] - config['status_last_sent'])
    minutes = round(total_seconds/60)
if minutes >= status_interval_minutes:
    send_discord = True
    print('send_discord = True. minutes >= status_interval_minutes')
    
print('last status: '+ str(minutes) +'min ago')
#######################################################

###discord send###
print('send_discord: '+ str(send_discord))
#print(discord_content)
if bool(send_discord):
    webhook = DiscordWebhook(url=config['discord_webhook'], content=discord_content)
    webhook_response = webhook.execute()
    print(webhook_response)
    del webhook, webhook_response
    ###update config
    config['status_last_sent'] = hs['now']
    UpdateConfig(config)

### clean up
print('************')
del hs,config