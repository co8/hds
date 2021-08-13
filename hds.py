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
# Set Crontab
# crontab -e
# run script every minute. log to file
# */1 * * * * cd ~/hds; python3 hds.py  >> ~/cron.log 2>&1
# @reboot cd ~/hds; python3 hds.py  >> ~/cron.log 2>&1
# - run at reboot for dedicated device, eg: RasPi Zero W
###
# install DiscordWebhook module
# % pip3 install discord-webhook
########

#######
# Command Line Arguments
# REPORT
# python3 hds.py report - send miner report
# RESET
# python3 hds.py reset - set last.send to 0
#######

####import libs
import sys
from os import stat
from time import time
import requests
import json
from datetime import datetime
from discord_webhook import DiscordWebhook

### vars
### FINE TUNE #####
status_lapse_hours = 6 #HOURS send status msg if X hours have lapsed since last message sent
report_interval_hours = 72 #HOURS scheduled miner report. time after last report sent
pop_status_minutes = 8 #MINUTES remove status msg when sending activity if activity is recent to last activity sent
##############
helium_api_endpoint = "https://api.helium.io/v1/"
config_file = "config.json"
activities = []
output_message = []
activity_history = []
hs = {}
status_lapse = 0
status_lapse_seconds = int(60 * 60 * status_lapse_hours)
report_interval_seconds = int(60 * 60 * report_interval_hours)
interval_pop_status_seconds = int(60 * pop_status_minutes) 
send = status_send = add_welcome = False
invalidReasonShortNames = {
    'witness_too_close' : 'Too Close',
    'witness_rssi_too_high' : 'RSSI Too High',
    'witness_rssi_below_lower_bound' : 'RSSI BLB'
}
rewardShortNames = {
    'poc_witnesses' : 'Witness',
    'poc_challengees' : 'Beacon',
    'poc_challengers' : 'Challenger',
    'data_credits' : 'Data'
}


#### functions

def localBobcatMinerReport():
    global status_send, output_message, report_interval_hours

    #send if next.report has been met
    if 'report' in config['next'] and hs['now'] > config['next']['report']:
        status_send = True
        print(f"{hs['time']} Bobcat Miner Report, every {report_interval_hours}hrs")

    if 'bobcat_local_endpoint' in config and bool(config['bobcat_local_endpoint']) and bool(status_send):

        #try to get json or return error
        try:
            #LIVE local data
            bobcat_miner_json = config['bobcat_local_endpoint'] +"miner.json"
            bobcat_request = requests.get(bobcat_miner_json)
            data = bobcat_request.json()

            ###LOCAL load miner.json
            #with open("miner.json") as json_data_file:
            #    data = json.load(json_data_file)

        except ValueError:  #includes simplejson.decoder.JSONDecodeError
            print(f"{hs['time']} Bobcat Miner Local API failure")
            quit()

        temp_alert = str.capitalize(data['temp_alert'])
        if temp_alert == 'Normal':
            temp_alert = '👍 '
        miner_state = str.capitalize(data['miner']['State'])
        if miner_state == 'Running':
            miner_state = '✅ 🏃‍♂️'
        block_height = str.split(data['height'][0])
        block_height = '📦'+ "{:,}".format(int(block_height[-1]))

        #helium OTA version
        helium_ota = data['miner']['Image']
        helium_ota = helium_ota.split("_")
        helium_ota = str(helium_ota[1])
        
        report = f"🧑‍🚀 **MINERity Report:** {miner_state} Temp: {temp_alert} Height:  {block_height}\n🎛 Firmware HELIUM: {helium_ota} / BOBCAT: {data['ota_version']}"
        output_message.insert(1, report) #insert at position 1 after status_msg

        #config values. repeat every X hours
        config['next']['report'] = hs['now'] + report_interval_seconds

        print(f"{hs['time']} bobcat miner report")

###load config.json vars
def loadConfig():
    global config, status_send
    with open(config_file) as json_data_file:
        config = json.load(json_data_file)
    
    #add framework for elements
    if not 'last' in config:
        config['last'] = {}
    if not 'next' in config:
        config['next'] = {}

    #command line arguments
    #send report if argument
    if 'report' in sys.argv:
        status_send = True
    if 'reset' in sys.argv:
        config['last']['send'] = 0 

    

def updateConfig():
    global config
    with open(config_file, "w") as outfile:
        json.dump(config, outfile)

def loadActivityHistory():
    global activity_history
    with open('activity_history.json') as json_data_file:
        activity_history = json.load(json_data_file)
        activity_history = set(activity_history) #list to set()

def updateActivityHistory():
    global activity_history

    #convert set to list
    activity_history = list(activity_history)

    #truncate history to 25 elements
    if len(activity_history) > 25 : 
        del activity_history[25:]

    #write file
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

def niceHotspotName(name):
    return name.replace('-', ' ').upper()

def niceHotspotInitials(name):
    return "".join(item[0].upper() for item in name.split())

def niceHNTAmount(amt):
    niceNum = .00000001
    niceNumSmall = 100000000
    
    # up to 3 decimal payments
    amt_output = '{:.3f}'.format(amt*niceNum)
    
    # 8 decimal places for micropayments
    #if amt > 0 and amt < 100000 :
    if amt in range(0, 100000):
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

def loadActivityData():
    global activities, config, hs, status_lapse, send, status_send

    #try to get json or return error
    try:
        #LIVE API data
        activity_endpoint = helium_api_endpoint +"hotspots/"+ config['hotspot'] +'/activity/'
        activity_request = requests.get(activity_endpoint)
        data = activity_request.json() 

        ###LOCAL load data.json
        #with open("data-short.json") as json_data_file:
        #   data = json.load(json_data_file)

    except ValueError:  #includes simplejson.decoder.JSONDecodeError
        print(f"{hs['time']} Helium API Activity JSON failure")
        quit()
    
    #set status_lapse if last.send exists
    if 'last' in config and 'send' in config['last']:
        status_lapse = int(config['last']['send'] + status_lapse_seconds)

    #add/update cursor to config
    if not 'cursor' in config or config['cursor'] != data['cursor']:
        config['cursor'] = data['cursor']


    #send if time lapse since last status met
    if hs['now'] >= status_lapse:
        print(f"{hs['time']} status msg")
        send = status_send = True
        
    #no data or status_send false
    elif not data['data'] and not bool(status_send):
        print(f"{hs['time']} no activities")
        quit()
    
    #set activities, set last.send, update config
    else:
        send = True
        activities = data['data']

###activity type poc_receipts_v1
def poc_receipts_v1(activity):
    witnesses = {}
    valid_text = '💩  Invalid'
    time = niceDate(activity['time'])

    #challenge accepted
    if 'challenger' in activity and activity['challenger'] == config['hotspot']:
        output_message.append(f"🏁  ...Challenged Beaconer  `{time}`")

    #beacon sent
    elif 'challengee' in activity['path'][0] and activity['path'][0]['challengee'] == config['hotspot']:
        wit_count = len(activity['path'][0]['witnesses'])
        wit_plural = ''
        valid_wit_count = 0
        if wit_count != 1:
            wit_plural = 'es'
        
        #beacon sent plus witness count and valid count
        for wit in activity['path'][0]['witnesses']:
            if bool(wit['is_valid']):
                valid_wit_count = valid_wit_count +1
        msg = f"🌋  Sent Beacon, {str(wit_count)} Witness{wit_plural}"
        if bool(wit_count):
            msg += f", {valid_wit_count} Valid"
        msg += f"  `{time}`"
        output_message.append(msg)
          

    #witnessed beacon plus valid or invalid and invalid reason
    elif 'witnesses' in activity['path'][0]:
            vw = 0 #valid witnesses
            valid_witness = False
            for w in activity['path'][0]['witnesses']:

                #valid witness count among witnesses
                if 'is_valid' in w and bool(w['is_valid']):
                    vw = vw +1

                if w['gateway'] == config['hotspot']:
                    witness_info = ''
                    if bool(w['is_valid']):
                        valid_witness = True
                        valid_text = '🤙  Valid'
                        witness_info = ', 1 of '+ str(len(activity['path'][0]['witnesses']))
                    elif 'invalid_reason' in w:
                        valid_text = '💩  Invalid'
                        witness_info = ', '+ niceInvalidReason(w['invalid_reason'])

                    #output_message.append(f"{valid_text} Witness{witness_info}  `{time}`")
            
            #add valid witness count among witnesses
            if bool(valid_witness) and vw > 1:
                witness_info += f", {vw} Valid"

            output_message.append(f"{valid_text} Witness{witness_info}  `{time}`")

    #other
    else:
        output_message.append(f"🏁  poc_receipts_v1() NO MATCH  `{time}`")


def loopActivities():
    global status_send

    if bool(activities) and not bool(status_send):

        #load history
        loadActivityHistory()

        for activity in activities:

            #skip if activity is in history
            if not bool(status_send) and (activity['hash'] in activity_history):
                continue #skip this element, continue for-loop

            #save activity hash if not found
            else:
                activity_history.add(activity['hash'])

            #activity time
            time = niceDate(activity['time'])
            
            #reward
            if activity['type'] == 'rewards_v2':
                for reward in activity['rewards']:
                    rew = rewardShortName(reward['type'])
                    amt = niceHNTAmount(reward['amount'])
                    output_message.append(f"🍪  Reward:  {rew.upper()}  🥓 {amt}  `{time}`")
            #transferred data
            elif activity['type'] == 'state_channel_close_v1':
                for summary in activity['state_channel']['summaries']:
                    output_message.append(f"🚛  Transferred {summary['num_packets']} Packets ({summary['num_dcs']} DC)  `{time}`")
            
            #...challenge accepted
            elif activity['type'] == 'poc_request_v1':
                output_message.append(f"🎲  Created Challenge...  `{time}`")

            #beacon sent, valid witness, invalid witness
            elif activity['type'] == 'poc_receipts_v1':
                poc_receipts_v1(activity)
            
            #other
            else:
                output_message.append(f"🚀  Activity: {activity['type']}  `{time}`")
#loopActivities()  

def loadHotspotDataAndStatusMsg():
    ###hotspot data
    global hs, config, add_welcome
    new_balance = new_reward_scale = new_height_percentage = False

    #try to get json or return error
    try:
        hs_endpoint = helium_api_endpoint +"hotspots/"+ config['hotspot']
        hs_request = requests.get(hs_endpoint)
        data = hs_request.json()
        if not data['data']:
            print(f"no hotspot data {hs['time']}")
            quit()
        else:
            hotspot_data = data['data']
        del hs_request

    except ValueError:  #includes simplejson.decoder.JSONDecodeError
        print(f"{hs['time']} Helium API Hotspot JSON failure")
        quit()

    ### hotspot data
    hs_add = {
        'owner' : hotspot_data['owner'],
        'name' : niceHotspotName(hotspot_data['name']),
        'status' : str(hotspot_data['status']['online']).upper(),
        'height' : hotspot_data['status']['height'],
        'block' : hotspot_data['block'],
        'reward_scale' : '{:.2f}'.format(round(hotspot_data['reward_scale'],2))
    }
    hs.update(hs_add)
    hs['initials'] = niceHotspotInitials(hs['name'])
    del data, hotspot_data

    #add/update cursor to config. supports hotspot ownership transfers
    if not 'owner' in config or config['owner'] != hs['owner']:
        config['owner'] = hs['owner']

    ###block height percentage
    #config_height_percentage = ''
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
    wallet_request = requests.get(helium_api_endpoint +"accounts/"+ hs['owner'])
    w = wallet_request.json()
    hs['balance'] = niceHNTAmount(w['data']['balance'])
    #if 'balance_last' not in config:
    #    config['balance_last'] = '0'
    ###add to config if new
    #if hs['balance'] != config['balance_last']:
    #    new_balance = True
    #    config['balance_last'] = hs['balance']
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
    status_msg = '📡  **'+ hs['initials'] +'**  🔥 '+ status_style +'  🥑 '+ height_percentage_style +'  🍕 '+ reward_scale_style +'  🥓 '+ balance_style
    
    #insert to top of output_message
    output_message.insert(0, status_msg)


def discordSend():
    global send, add_welcome

    #send if no last.send in config
    if 'last' in config and not 'send' in config['last']:
        send = add_welcome = True

    #send if more than 1 (default) msg
    elif len(output_message) > 1:
        send = True
    
    #don't send 
    elif not bool(status_send):
        send = False
        print(f"{hs['time']} repeat activities")
        quit()


    #add welcome msg to output if no config[last][send]
    if bool(add_welcome):
        output_message.insert(0, f"🤙 **{hs['name']}   [ 📡  {hs['initials']} ]**")

    if bool(send):

        #only send activity, remove status if recently sent
        if 'last' in config and 'send' in config['last'] and hs['now'] < (config['last']['send'] + interval_pop_status_seconds):
            output_message.pop(0)

        #update last.send to be last status sent
        config['last']['send'] = hs['now']
        updateConfig()

        discord_message = '\n'.join(output_message)

        webhook = DiscordWebhook(url=config['discord_webhook'], content=discord_message)
        ###send
        webhook_response = webhook.execute()
        return webhook_response.reason
    


#########################
### main
def main():
    loadConfig()
    getTime()
    loadActivityData()

    #if activity data...
    loadHotspotDataAndStatusMsg()  
    loopActivities()
    localBobcatMinerReport()
    discord_response_reason = discordSend()

    #update history
    updateActivityHistory()

    #status log
    print(f"{hs['time']} msgs:{str(len(output_message))} act:{str(len(activities))} discord:{discord_response_reason}")


### execute main() if main is first module
if __name__ == '__main__':
    main()