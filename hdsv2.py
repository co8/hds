#!/usr/bin/python3

############################
# 08/21 JULY
# co8.com 
# enrique r grullon
# e@co8.com
# discord: co8#1934 
# HDS v2 - Hotspot Discord Status
############################

########
# crontab -e
# check every 5 minutes. log to file
# */1 * * * * cd ~/hds; python3 hdsv2.py  >> ~/cronv2.log 2>&1
# @reboot cd ~/hds; python3 hdsv2.py  >> ~/cronv2.log 2>&1
# - run at reboot for dedicated device, eg: RasPi Zero W
###
# install DiscordWebhook module
# % pip3 install discord-webhook
########

####import libs
from os import stat
from time import time
import requests
import json
from datetime import datetime
from discord_webhook import DiscordWebhook

### vars
config_file = "configv2.json"
activities = output_message = activity_history = []
hs = {} #main dict
status_lapse = 0
status_lapse_hours = 1
status_lapse_seconds = int(60 * 60 * 60 * status_lapse_hours)
send = status_send = False
invalidReasonShortNames = {
    'witness_too_close' : 'Too Close',
    'witness_rssi_too_high' : 'RSSI Too High',
    'witness_rssi_below_lower_bound' : 'RSSI b.l.b.'
}
rewardShortNames = {
    'poc_witnesses' : 'Witness',
    'poc_challengees' : 'Beacon',
    'poc_challengers' : 'Challenger',
    'data_credits' : 'Data'
}


###load config.json vars
def loadConfig():
    global config
    with open(config_file) as json_data_file:
        config = json.load(json_data_file)

def updateConfig():
    global config
    with open(config_file, "w") as outfile:
        json.dump(config, outfile)

def loadActivityHistory():
    global activity_history
    with open('activity_history.json') as json_data_file:
        activity_history = json.load(json_data_file)

def updateActivityHistory():
    global activity_history

    #truncate to newest 10 activities
    if len(activity_history) > 25: 
        del activity_history[25:]

    with open('activity_history.json', "w") as outfile:
        json.dump(activity_history, outfile)

def getTime():
    global hs
    ###Time functions
    now = datetime.now()
    hs['now'] = round(datetime.timestamp(now))
    hs['time'] = str(now.strftime("%H:%M %D"))

###functions
def niceDate(time):
    timestamp = datetime.fromtimestamp(time)
    return timestamp.strftime("%H:%M %d/%b").upper()
    #return datetime.fromtimestamp(time.strftime("%H:%M %d/%b").upper())

def niceHotspotName(name):
    return name.replace('-', ' ').upper()

def niceHotspotInitials(name):
    return "".join(item[0].upper() for item in name.split())

def niceHNTAmount(amt):
    niceNum = .00000001
    niceNumSmall = 100000000
    # up to 3 decimal payments
    amt_output = '{:.3f}'.format(amt*niceNum) #.rstrip('0')
    
    # 8 decimal places for micropayments
    if amt > 0 and amt < 100000 :
        amt_output = '{:.8f}'.format(amt / niceNumSmall).rstrip('0')
        amt_output = f"`{amt_output}`"
    return str(amt_output)

#invalid reason nice name, or raw reason if not in dict
def niceInvalidReason(ir):
    output = str(ir)
    if ir in invalidReasonShortNames:
        output = invalidReasonShortNames[ir]
    return output

###activity type name to short name    
def rewardShortName(reward_type):
    output = reward_type.upper()
    if reward_type in rewardShortNames:
        output = rewardShortNames[reward_type]  
    return output

def LOCAL_loadActivityData():
    global activities

    ###load data.json
    with open("data-short.json") as json_data_file:
        data = json.load(json_data_file)
    
    if not data['data']:
        print(f"no activities data {hs['time']}")
        quit()
    else:
        activities = data['data']
    del data

def loadActivityData():
    global activities, config, hs, status_lapse, send, status_send
    activity_endpoint = config['api_endpoint'] +"hotspots/"+ config['hotspot'] +'/activity/'
    activity_request = requests.get(activity_endpoint)
    data = activity_request.json()
    
    #set status_lapse if last_activity_time exists
    if 'last_activity_time' in config:
        status_lapse = int(config['last_activity_time'] + status_lapse_seconds)

    #send if time lapse since last status met
    #if hs['now'] > status_lapse:
    #    print(f"{hs['time']} status msg")
    #    send = status_send = True
    #    update last_activity_time to be last status sent
    #    config['last_activity_time'] = hs['now']
    #    updateConfig()
        
    #no data or status_send false
    if not data['data']: #or not bool(status_send):
        print(f"{hs['time']} no activities")
        quit()
  
    #data, but last_activity_time matches data['data'][0][time]
    #if data['data'] and 'last_activity_time' in config and config['last_activity_time'] == data['data'][0]['time']:
    #   print(f"{hs['time']} repeat activities")
    #   quit()
    
    #set activities, set last_activity_time, update config
    else:
        send = True
        activities = data['data']

        #update config
        #config['last_activity_time'] = data['data'][0]['time']
        #updateConfig()
        

###activity type poc_receipts_v1
def poc_receipts_v1(activity):
    witnesses = {}
    valid_text = '💩  Invalid'
    time = niceDate(activity['time'])

    #challenge accepted
    if 'challenger' in activity and activity['challenger'] == config['hotspot']:
        output_message.append(f"🏓  ...Challenged Beaconer  `{time}`")

    #beacon sent
    elif 'challengee' in activity['path'][0] and activity['path'][0]['challengee'] == config['hotspot']:
        wit_count = len(activity['path'][0]['witnesses'])
        wit_plural = ''
        valid_wit_count = 0
        if wit_count != 1:
            wit_plural = 'es'
        
        for wit in activity['path'][0]['witnesses']:
            if bool(wit['is_valid']):
                valid_wit_count = valid_wit_count +1
        msg = f"🌋  Sent Beacon, {str(wit_count)} Witness{wit_plural}"
        if bool(valid_wit_count):
            msg += f", {valid_wit_count} Valid"
        msg += f"  `{time}`"
        output_message.append(msg)
          

    #witness of beacon - valid and invalid
    elif 'witnesses' in activity['path'][0]:
            for w in activity['path'][0]['witnesses']:
                if w['gateway'] == config['hotspot']:
                    witness_info = ''
                    if bool(w['is_valid']):
                        valid_witness = True
                        valid_text = '🤘  Valid'
                        witness_info = ', 1 of '+ str(len(activity['path'][0]['witnesses']))
                    elif 'invalid_reason' in w:
                        valid_text = '💩  Invalid'
                        witness_info = ', '+ niceInvalidReason(w['invalid_reason'])

                    output_message.append(f"{valid_text} Witness{witness_info}  `{time}`")
    
    #other
    else:
        output_message.append(f"🏁  poc_receipts_v1() NO MATCH  `{time}`")

def loopActivities():
    global status_send
    if not bool(status_send):
        for activity in activities:

            #skip if activity is in history
            if (activity['hash'] in activity_history):
                continue #skip this element, continue for-loop

            #save activity hash if not found
            else:
                activity_history.append(activity['hash'])

            #activity time
            time = niceDate(activity['time'])
            
            #reward
            if activity['type'] == 'rewards_v2':
                for reward in activity['rewards']:
                    rew = rewardShortName(reward['type'])
                    amt = niceHNTAmount(reward['amount'])
                    output_message.append(f"🍪  REWARD: {rew}  🥓 {amt}  `{time}`")
            #transferred data
            elif activity['type'] == 'state_channel_close_v1':
                for summary in activity['state_channel']['summaries']:
                    output_message.append(f"🚛  Transferred {summary['num_packets']} Packets ({summary['num_dcs']} DC)  `{time}`")
            
            #...challenge accepted
            elif activity['type'] == 'poc_request_v1':
                output_message.append(f"🎲  Created Challenge...  `{time}`")

            #beacon, valid witness, invalid witness
            elif activity['type'] == 'poc_receipts_v1':
                poc_receipts_v1(activity)
            
            #other
            else:
                output_message.append(f"🏁  Activity: {activity['type']}  `{time}`")
#loopActivities()  

def loadHotspotDataAndStatusMsg():
    ###hotspot data
    global hs
    new_balance = new_reward_scale = new_height_percentage = False

    hs_endpoint = config['api_endpoint'] +"hotspots/"+ config['hotspot']
    hs_request = requests.get(hs_endpoint)
    data = hs_request.json()
    if not data['data']:
        print(f"no hotspot data {hs['time']}")
        quit()
    else:
        hotspot_data = data['data']
    del hs_request

    ### hotspot data
    hs_add = {
        'owner' : hotspot_data['owner'],
        'name' : niceHotspotName(hotspot_data['name']),
        'status' : str(hotspot_data['status']['online']).upper(),
        'height' : hotspot_data['status']['height'],
        'block' : hotspot_data['block'],
        'reward_scale' : '{:.2f}'.format(round(hotspot_data['reward_scale'],2)),
        'witness_count' : ''
    }
    hs.update(hs_add)
    hs['initials'] = niceHotspotInitials(hs['name'])
    del data, hotspot_data

    ###block height percentage
    config_height_percentage = ''
    #if 'height_percentage_last' in config:
    #   config_height_percentage = config['height_percentage_last']
    hs['height_percentage'] = round(hs['height'] / hs['block'] * 100, 2)
    if(hs['height_percentage'] >= 100):
        hs['height_percentage'] = 100
    if hs['height_percentage'] > 98:
        hs['height_percentage'] = "*NSYNC"
    else:
        hs['height_percentage'] = str(hs['height_percentage']) +'%'
    
    ###wallet data
    wallet_request = requests.get(config['api_endpoint'] +"accounts/"+ hs['owner'])
    w = wallet_request.json()
    hs['balance'] = niceHNTAmount(w['data']['balance'])
    if 'balance_last' not in config:
        config['balance_last'] = '0'
    ###add to config if new
    if hs['balance'] != config['balance_last']:
        new_balance = True
        #config['balance_last'] = hs['balance']
    del wallet_request, w
    
    #### STYLE
    ### bold balance if has changed
    balance_style = hs['balance'] #+' hnt'
    #if bool(new_balance):
    #    balance_style = '**'+ balance_style +'**'
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
    discord_content = ' 📡 **'+ hs['initials'] +'** 🔥 '+ status_style +' 🥑 '+ height_percentage_style +' 🍕'+ reward_scale_style +'  🥓 '+ balance_style
        
    output_message.insert(0, discord_content)

    #if not 'last_activity_time' in config:
    #    output_message.insert(0, f"🤙 **{hs['name']}   [ {hs['initials']} ]**  🤘")

def discordSend():
    global send

    #send if no last_activity_time in config
    if not 'last_activity_time' in config:
        send = True

    #send if more than 1 (default) msg
    elif len(output_message) > 1:
        send = True
    
    #don't send if only 1 element - Status msg only
    elif len(output_message) == 1:
        send = False
        print(f"{hs['time']} repeat activities (history)")
        quit()

    if bool(send):
        msg = '\n'.join(output_message)
        webhook = DiscordWebhook(url=config['discord_webhook'], content=msg)
        ###send
        webhook_response = webhook.execute()
        return webhook_response.reason



#########################
### main
def main():
    loadConfig()
    loadActivityHistory()
    getTime()
    loadActivityData()

    #if activity data...
    loadHotspotDataAndStatusMsg()   
    loopActivities()
    discord_response_reason = discordSend()

    #update history
    updateActivityHistory()

    #status log
    print(f"{hs['time']} msgs:{str(len(output_message))} act:{str(len(activities))} discord: {discord_response_reason}")

### execute main() if main is first module
if __name__ == '__main__':
    main()
