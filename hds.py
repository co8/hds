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
###vars
status_interval_minutes = 238 #4hrs
new_activity = send_discord = welcome = new_balance = new_reward_scale = new_height_percentage = False
niceNum = .00000001
niceNumSmall = 100000000
activity_data = activity_cursor = discord_content = ''

api_endpoint = 'https://api.helium.io/v1/'

###functions
def NiceName(name):
    return name.replace('-', ' ').upper()

def NameInitials(name):
    nicename = NiceName(name)
    return "".join(item[0].upper() for item in nicename.split())

def NiceBalance(balance):
    bal = '{:.3f}'.format(balance*niceNum) #.rstrip('0')
    if balance > 0 and balance < 100000 :
        bal = '{:.8f}'.format(balance / niceNumSmall).rstrip('0')
    return str(bal)

def UpdateConfig(config):
    with open("config.json", "w") as outfile:
        json.dump(config, outfile)

### Activity Short Names
typeShortNames = {
    'poc_receipts_v1' : {
        'beacon' : 'PoC  🌋  Sent Beacon', #beacon plus witness count, plus valid count
        'valid_witness' : 'PoC  🐵  Valid Witness',
        'invalid_witness' : 'PoC  🙈  Invalid Witness',
        'challenge_accepted' : 'PoC  🏓  Created Challenge Accepted'
    },
    'poc_request_v1' : 'PoC  🤼  Created Challenge...',
    'rewards_v2' : ' 🌊  REWARD  🏄‍♀️ ',
    'state_channel_close_v1' : 'Transferred  🚛  Data Packets'
}
###activity type poc_request_v1 - which is it?
def whichPocRequestV1(activity_type):
    print('whichPocRequestV1 activity_type: '+ activity_type)
    witnesses = {}
    valid_witnesses = 0
    output = 'challenge_accepted'
    has_witnesses = show_witnesses = False

    if 'witnesses' in activity_data['path'][0]:
        witnesses = activity_data['path'][0]['witnesses']
        hs['witness_count'] = len(witnesses)
        has_witnesses = True
        print('has witnesses: '+ str(hs['witness_count']))
    
    #is beacon?
    if activity_data['path'][0]['challengee'] == config['hotspot']:
        output = 'beacon'   
        show_witnesses = True  
        print('poc_receipt_v1: ' + output)
        hs['witness_count'] = len(witnesses)
    else:
        print('not beacon')

    if bool(has_witnesses):
        #is witness? valid or invalid?
        #check for hotspot in witness list. check valid
        print('***********')
        print('looping thru witnesses')
        #x = any( w['owner'] == config['owner'] for w in witnesses )
        for w in witnesses:
            #if witness, check if valid or invalid
            if w['owner'] == config['owner']:
                print('yes, hotspot is a witness')
                print('is_valid: '+ str(w['is_valid']))             
                if 'is_valid' in w and bool(w['is_valid']):
                    output = 'valid_witness'
                else:
                    output = 'invalid_witness'
                print(w['owner'] +': '+ output)
            #if beacon, how many invalid witnesses
            if output == 'beacon' and 'is_valid' in w and bool(w['is_valid']):
                valid_witnesses = valid_witnesses +1 #add 1 to invalid witness count

    else:
        print('no witnesses')
    
    #print('output type BEFORE: '+ output)
    #exit()
    output = typeShortNames[activity_type][output]
    print('output type: '+ str(output))
    #if beacon, add witness and pluralize based on count
    if bool(show_witnesses):
        output += ', '+ str(hs['witness_count']) + " Witness"
        if hs['witness_count'] != 1 : 
            output += 'es'
        if bool(hs['witness_count']):
            output += ', '+ str(valid_witnesses) +' Valid'
    return output

###activity type name to short name    
def ActivityShortName(activity_type):
    if activity_type == 'poc_receipts_v1':
        #which PoC Receipt is it?
        output = whichPocRequestV1(activity_type)
    elif activity_type in typeShortNames:
        output = typeShortNames[activity_type]
    else:
        output = activity_type.upper()
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
    'witness_count' : ''
}
hs['initials'] = NameInitials(hs['name'])
del hotspot_request, hotspot_response

###check for change in reward_scale
config_reward_scale = ''
if 'reward_scale_last' in config:
    config_reward_scale = config['reward_scale_last']
if hs['reward_scale'] != config_reward_scale:
    new_reward_scale = True
    config['reward_scale_last'] = hs['reward_scale']
    UpdateConfig(config)


### get NOW
now = datetime.now()
hs['now'] = round(datetime.timestamp(now))
hs['time'] = str(now.strftime("%D %H:%M"))
del now

###block height percentage
config_height_percentage = ''
if 'height_percentage_last' in config:
    config_height_percentage = config['height_percentage_last']
hs['height_percentage'] = round(hs['height'] / hs['block'] * 100, 2)
if(hs['height_percentage'] >= 100):
    hs['height_percentage'] = 100
if hs['height_percentage'] > 98:
    hs['height_percentage'] = "*NSYNC"
else:
    hs['height_percentage'] = str(hs['height_percentage']) +'%'

#check for change in height_percentage
if hs['height_percentage'] != config_height_percentage:
    new_height_percentage = True
    config['height_percentage_last'] = hs['height_percentage']
    UpdateConfig(config)
    
###wallet data
wallet_request = requests.get(api_endpoint +"accounts/"+ hs['owner'])
w = wallet_request.json()
hs['balance'] = NiceBalance(w['data']['balance'])
if 'balance_last' not in config:
    config['balance_last'] = '0'
###add to config if new
if hs['balance'] != config['balance_last']:
    new_balance = True
    #print('config.balance_last: '+ str(config['balance_last']) +'\nhs.balance: '+ str(hs['balance']) +'\nnew_balance: '+ str(new_balance))
    config['balance_last'] = hs['balance']
    UpdateConfig(config)
del wallet_request, w

#### New User Welcome
if 'owner' not in config:
    print('Adding Welcome msg')
    send_discord = welcome = True
    config['owner'] = hs['owner']
    discord_content += '🤙 **'+ hs['name'] +'   [ '+ hs['initials'] +' ]**  🤘\n'

    
###activity data
activity_endpoint = api_endpoint +"hotspots/"+ config['hotspot'] +'/activity/'
#get fresh activity
activity_request = requests.get(activity_endpoint)
activity = activity_request.json() 
###add activity cursor to config
config['activity_cursor'] = activity['cursor']
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

# if activity data, get activity data
if bool(activity['data']):
    #if data in first request, use that new data
    activity_data_all = activity['data']

    #dev - list instead of single
    activity_data = activity_data_all[0]
    #activity_data = activity_data_all

    print('ln250 activity[data] count: ' + str(len(activity_data_all))) #count for future dev
    send_discord = True

elif send_discord == False and 'status_last_sent' in config: 
    # quit and done until next check. 
    # don't get activity if sent activity and no new data
    print(hs['time'] +' Nothing new. Quietly Quiting. Will try again Later 🤙')
    print('************')
    quit()
else:
    #get activity using cursor
    print('getting activity with cursor') 
    activity_cursor_request = requests.get(activity_endpoint +'?cursor='+ config['activity_cursor'])
    activity = activity_cursor_request.json()
    
    ###get ALL activity data
    activity_data_all = activity['data']
    print('ln254 activity[data] via cursor count: ' + str(len(activity_data_all))) #count for future dev
    ###get last activity only
    activity_data = activity_data_all.pop(0) #only first element
    #add activity_cursor and write to config.json
    print('writing activity cursor to config')
    UpdateConfig(config)
    del activity_data_all, activity_cursor_request
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
hs_rewards = {}
if 'rewards' in activity_data:
    print('YES rewards in actvity')
    amount = activity_data['rewards'][0]['amount']
    hs['rewards'] = {
        'amount' : amount,
        'type' : activity_data['rewards'][0]['type'],
        'time' : activity_data['time'],
        'amount_nice' : NiceBalance(amount),
    }
else:
    print('no rewards in activity')

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
### bold balance if has changed
#balance_style = '`'+ hs['balance'] +'`' #add codeblock formatting
balance_style = hs['balance'] #+' hnt'
if bool(new_balance):
    balance_style = '**'+ balance_style +'**'
### bold reward_scale if has changed
reward_scale_style = hs['reward_scale']
if bool(new_reward_scale):
    reward_scale_style = '**'+ reward_scale_style +'**'
### bold height_percentage if has changed
height_percentage_style = hs['height_percentage']
if bool(new_height_percentage):
    height_percentage_style = '**'+ height_percentage_style +'**'
### bold status if not online
status_style = hs['status']
if hs['status'] != 'ONLINE':
    status_style = '**'+ hs['status'] +'**'

#default status msg
discord_content += '📡 **'+ hs['initials'] +'** 🔥 '+ status_style +' 🥑 '+ height_percentage_style +' 🍕'+ reward_scale_style +' 🥓 '+ balance_style

#function and loop all activities
### compose new activity
if bool(new_activity):
    send_discord = True
    print('adding new activity msg')
    activity_time = datetime.fromtimestamp(hs['activity_last_time']).strftime("%H:%M %d/%b").upper()
    #for first status msg
    discord_content += '\n'
    if bool(welcome):
        discord_content += 'Last:'
    else:
        discord_content += '🚀'

    ###add reward if exists
    if_reward = ''
    if 'rewards' in hs:
        if_reward = '  🥓 `'+ NiceBalance(hs['rewards']['amount']) +'`'
    ### add reward type
    shortname = ActivityShortName(config['activity_last_type'])

    discord_content += ' **'+ shortname +'**'+ if_reward +'  '+ activity_time
    

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
    #print('send_discord = True. minutes >= status_interval_minutes')
    
print('last status: '+ str(minutes) +'min ago')
#######################################################

###discord send###
#print('send_discord: '+ str(send_discord))
#print(discord_content)
if bool(send_discord):
    webhook = DiscordWebhook(url=config['discord_webhook'], content=discord_content)
    ###send
    webhook_response = webhook.execute()
    print(webhook_response)
    del webhook, webhook_response
    ###update config
    config['status_last_sent'] = hs['now']
    UpdateConfig(config)

### clean up
print(hs['time'])
print('************')
del hs,config