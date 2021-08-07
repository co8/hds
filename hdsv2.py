
####import libs
from time import time
import requests
import json
from datetime import datetime

###temp config
config = {
    'hotspot' : '112MWdscG3DjHTxdCrtuLkkXNSbxCkbqkuiu8X9zFDwsBfa2teCD',
    'owner' : '14hriz8pmxm51FGmk1nuijHz6ng9z9McfJZgsg4yxzF2H7No3mH'
}

### vars
activities = output_message = []
hs = {} #main dict
welcome = True
invalidReasonShortNames = {
    'witness_too_close' : 'too close',
    'witness_rssi_too_high' : 'RSSI too high',
    'witness_rssi_below_lower_bound' : 'RSSI below lower bound'
}
rewardShortNames = {
    'poc_witnesses' : 'Witness',
    'poc_challengees' : 'Beacon',
    'poc_challengers' : 'Challenger',
    'data_credits' : 'Data'
}

###Time functions
now = datetime.now()
hs['now'] = round(datetime.timestamp(now))
hs['time'] = str(now.strftime("%H:%M %D"))
del now

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
    return str(amt_output)

#invalid reason nice name, or raw reason if not in dict
def niceInvalidReason(ir):
    output = str(ir)
    if ir in invalidReasonShortNames:
        output = invalidReasonShortNames[ir]
    return output

###activity type name to short name    
def rewardShortName(reward_type):
    if reward_type in rewardShortNames:
        output = rewardShortNames[reward_type]
    else:
        output = reward_type.upper()
    return output

###activity type poc_receipts_v1
def poc_receipts_v1(activity):
    witnesses = {}
    beacon_valid_witnesses = 0
    output = 'challenge_accepted'
    invalid_witness_reason = ''
    has_witnesses = beacon_show_witnesses = valid_witness = False
    valid_text = '💩  Invalid'

    time = niceDate(activity['time'])

    #challenge accepted
    if 'challenger' in activity and activity['challenger'] == config['hotspot']:
        output_message.append(f" 🤼  ...Challenge Accepted {time}")

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
        msg = f" 🌋  Beacon Sent, {str(wit_count)} Witness{wit_plural}"
        if bool(valid_wit_count):
            msg += f", {valid_wit_count} Valid"
        msg += f" {time}"
        output_message.append(msg)
          

    #witness - valid and invalid
    elif 'witnesses' in activity['path'][0]:
            witnesses = activity['path'][0]['witnesses']
            for w in witnesses:
                if w['gateway'] == config['hotspot']:
                    witness_info = ''
                    if bool(w['is_valid']):
                        valid_witness = True
                        valid_text = '🤘  Valid'
                        witness_info = ', 1 of '+ str(len(witnesses))
                    elif 'invalid_reason' in w:
                        valid_text = '💩  Invalid'
                        witness_info = ' ('+ niceInvalidReason(w['invalid_reason']) +')'

                    output_message.append(f" {valid_text} Witness{witness_info} {time}")
    
    #other
    else:
        output_message.append(f" 🏁  poc_receipts_v1() NO MATCH {time}")

def loadActivityData():
    global activities
    ###load data.json
    with open("data.json") as json_data_file:
        data = json.load(json_data_file)
    if not data['data']:
        print(f"no activities data {hs['time']}")
        quit()
    else:
        activities = data['data']
    del data

def loadHotspotData():
    ###hotspot data
    global hs
    ###load data.json
    with open("hotspot.json") as json_data_file:
        data = json.load(json_data_file)
    if not data['data']:
        print(f"no hotspot data {hs['time']}")
        quit()
    else:
        hotspot_data = data['data']
    
    ### hotspot data
    hs = {
        'owner' : hotspot_data['owner'],
        'name' : niceHotspotName(hotspot_data['name']),
        'status' : str(hotspot_data['status']['online']).upper(),
        'height' : hotspot_data['status']['height'],
        'block' : hotspot_data['block'],
        'reward_scale' : '{:.2f}'.format(round(hotspot_data['reward_scale'],2)),
        'witness_count' : ''
    }
    hs['initials'] = niceHotspotInitials(hs['name'])
    del data, hotspot_data
    if bool(welcome):
        output_message.insert(0, f" 🤙 **{hs['name']}   [ {hs['initials']} ]**  🤘")
    else:
        output_message.insert(0, f"{hs['initials']} status message here")
    

########################################################


def loopActivities():
    for activity in activities:
        
        #activity time
        time = niceDate(activity['time'])
        
        #reward
        if activity['type'] == 'rewards_v2':
            for reward in activity['rewards']:
                rew = rewardShortName(reward['type'])
                amt = niceHNTAmount(reward['amount'])
                output_message.append(f" 🌊  REWARD: {rew}  🥓  {amt} {time}")
        #transferred data
        elif activity['type'] == 'state_channel_close_v1':
            for summary in activity['state_channel']['summaries']:
                output_message.append(f" 🚛  Transferred {summary['num_packets']} Packets ({summary['num_dcs']} DC) {time}")
        
        #...challenge accepted
        elif activity['type'] == 'poc_request_v1':
            output_message.append(f" 🏓  Created Challenge... {time}")

        #beacon, valid witness, invalid witness
        elif activity['type'] == 'poc_receipts_v1':
            poc_receipts_v1(activity)
        
        #other
        else:
            output_message.append(f" 🏁  Activity: {activity['type']} {time}")
#loopActivities()       

#########################
### main
def main():
    loadActivityData()
    loadHotspotData()
    loopActivities()

    #count
    print('activities: '+ str(len(activities)))
    print('output_message count:'+ str(len(output_message)))
    print(*output_message, sep="\n")

### execute main() if main is first module
if __name__ == '__main__':
    main()
