#!/usr/bin/python3

############################
# HDS - Hotspot Discord Status
# https://github.com/co8/hds
#
# co8.com
# enrique r grullon
# e@co8.com
# discord: co8#1934
############################

########
# Set Crontab
# crontab -e
# - run script every minute. log to file
# */1 * * * * cd ~/hds; python3 hds.py >> cron.log 2>&1
########


########
# install Discord-Webhook module
# % pip3 install discord-webhook
########

#######
# Command Line Arguments
# REPORT
# python3 hds.py report - send miner report (if set Bobcat_local_endpoint)
# RESET
# python3 hds.py reset
#######

# modules/libraries
import sys
import time
import requests
import json
from datetime import datetime
from discord_webhook import DiscordWebhook

####
# Notes:
# To Add: Private methods, functions and data members
# _ : you shouldn’t access this method because it’s not part of the API
# __ : mangle the attribute names of a class to avoid conflicts of attribute names between classes
####

### vars
# override default values in config.json
wellness_check_hours = 8  # Default 8 hours. send status msg if X hours have lapsed since last message sent. slows miner, don't abuse
report_interval_hours = 72  # HOURS scheduled miner report. time after last report sent. slows miner, don't abuse
#
#
pop_status_minutes = 8  # MINUTES remove status msg when sending activity if activity is recent to last activity sent. keep discord tidy
helium_api_endpoint = "https://api.helium.io/v1/"
helium_explorer_tx = "https://explorer.helium.com/txns/"
config_file = "config.json"
activities = []
output_message = []
activity_history = []
hs = {}
wellness_check = history_repeats = wellness_check_seconds = 0
report_interval_seconds = output_message_length = 0
interval_pop_status_seconds = int(60 * pop_status_minutes)
send = send_report = add_welcome = send_wellness_check = False
invalid_reason_short_names = {
    "witness_too_close": "Too Close",
    "witness_rssi_too_high": "RSSI Too High",
    "witness_rssi_below_lower_bound": "RSSI BLB",
}
reward_short_names = {
    "poc_witnesses": "Witness",
    "poc_challengees": "Beacon",
    "poc_challengers": "Challenger",
    "data_credits": "Data",
}


#### functions


def local_bobcat_miner_report():
    # only run if bobcat_local_endpoint is set
    if "bobcat_local_endpoint" in config and bool(config["bobcat_local_endpoint"]):

        global send_report, output_message, report_interval_hours, add_welcome

        # send if next.report has been met
        if "report" in config["next"] and hs["now"] > config["next"]["report"]:
            send_report = True
            hour_plural = "s" if report_interval_hours != 1 else ""
            interval_msg = f"`⏰ Scheduled Miner Report, every {report_interval_hours}hr{hour_plural} `"
            output_message.insert(0, interval_msg)
            print(
                f"\n{hs['time']} report interval met, every {report_interval_hours}hrs",
                end="",
            )

        if bool(send_report) or bool(add_welcome):
            # if 'bobcat_local_endpoint' in config and bool(config['bobcat_local_endpoint']) and bool(send_report):

            # try to get json or return error
            status = ""
            try:
                # LIVE local data
                bobcat_miner_json = config["bobcat_local_endpoint"] + "miner.json"
                bobcat_request = requests.get(bobcat_miner_json)
                data = bobcat_request.json()

                ### Dev only
                ###LOCAL load miner.json
                # with open("miner.json") as json_data_file:
                #    data = json.load(json_data_file)
            except requests.RequestException:
                status = "Connectivity"
            except ValueError:  # includes simplejson.decoder.JSONDecodeError
                status = "Parsing JSON"
            except (IndexError, KeyError):
                status = "JSON format"

            if bool(status):
                print(f"\n{hs['time']} Bobcat API Error: {status}")

            else:

                temp_alert = (
                    "👍 "
                    if data["temp_alert"] == "normal"
                    else str.capitalize(data["temp_alert"])
                )
                miner_state = (
                    "✅ + 🏃‍♂️"
                    if data["miner"]["State"] == "running"
                    else str.capitalize(data["miner"]["State"])
                )

                # block height
                block_height = str.split(data["height"][0])
                block_height = "{:,}".format(int(block_height[-1]))

                if (
                    "report" in config["last"]
                    and "block_height" not in config["last"]["report"]
                ):
                    config["last"]["report"]["block_height"] = ""
                ###add to config if new
                if (
                    "report" in config["last"]
                    and block_height != config["last"]["report"]["block_height"]
                ):
                    config["last"]["report"]["block_height"] = block_height
                    block_height = f"**{block_height}**"

                # helium OTA version
                ota_helium = data["miner"]["Image"]
                ota_helium = ota_helium.split("_")
                ota_helium = str(ota_helium[1])
                if "ota_helium" not in config["last"]["report"]:
                    config["last"]["report"]["ota_helium"] = ""
                if ota_helium != config["last"]["report"]["ota_helium"]:
                    config["last"]["report"]["ota_helium"] = ota_helium
                    ota_helium = f"**{ota_helium}**"

                # bobcat OTA version
                ota_bobcat = data["ota_version"]
                if "ota_bobcat" not in config["last"]["report"]:
                    config["last"]["report"]["ota_bobcat"] = ""
                if ota_bobcat != config["last"]["report"]["ota_bobcat"]:
                    config["last"]["report"]["ota_bobcat"] = ota_bobcat
                    ota_bobcat = f"**{ota_bobcat}**"

                report = f"🔩🔩  **MINERity Report : {hs['time']}**  🔩🔩\nStatus: {miner_state} Temp: {temp_alert} Height: 📦 {block_height}\nFirmware: Helium {ota_helium} | Bobcat {ota_bobcat}"
                output_message.append(report)

                # config values. repeat every X hours
                config["next"]["report"] = hs["now"] + report_interval_seconds
                config["next"]["report_nice"] = nice_date(config["next"]["report"])

                print(f"\n{hs['time']} bobcat miner report", end="")


###load config.json vars
def load_config():
    global config, send_report, activity_history, wellness_check_hours, report_interval_hours, wellness_check_seconds, report_interval_seconds, add_welcome
    with open(config_file) as json_data_file:
        config = json.load(json_data_file)

    # wellness_check_hours - default sets config, or uses config value
    if "wellness_check_hours" in config:
        wellness_check_hours = config["wellness_check_hours"]
    # else:
    #    config["wellness_check_hours"] = wellness_check_hours
    wellness_check_seconds = int(60 * 60 * wellness_check_hours)

    # report_interval_hours - default sets config, or uses config value
    if "report_interval_hours" in config:
        report_interval_hours = config["report_interval_hours"]
    # else:
    #    config["report_interval_hours"] = report_interval_hours
    report_interval_seconds = int(60 * 60 * report_interval_hours)

    # add structure for elements
    if "name" not in config:
        config["name"] = ""
    if "initials" not in config:
        config["initials"] = ""
    if "owner" not in config:
        config["owner"] = ""
    if "cursor" not in config:
        config["cursor"] = ""
    if "last" not in config:
        config["last"] = {}
    if "next" not in config:
        config["next"] = {}
    if "report" not in config["last"]:
        config["last"]["report"] = {}

    # send if no last.send in config
    if "send" not in config["last"]:
        add_welcome = True

    # command line arguments
    # send report if True
    send_report = True if "report" in sys.argv else False

    # reset hds. only clear config last/next and activity_history.
    if "reset" in sys.argv:
        config["last"] = config["next"] = {}
        config["cursor"] = ""
        update_config()
        activity_history = []
        update_activity_history()


def update_config():
    global config
    with open(config_file, "w") as outfile:
        json.dump(config, outfile)


def load_activity_history():
    global activity_history
    with open("activity_history.json") as json_data_file:
        activity_history = json.load(json_data_file)


def update_activity_history():
    global activity_history, hs

    if bool(activity_history):

        # trim history. remove first 15 (oldest) elements if over 50 elements
        if len(activity_history) > 50:
            print(f"\n{hs['time']} trimming activity_history", end="")
            del activity_history[:15]

        # save history details to config
        if "activity_history" not in config["last"]:
            config["last"]["activity_history"] = {}

        config["last"]["activity_history"] = {
            "count": len(activity_history),
            "last": hs["now"],
            "last_nice": nice_date(hs["now"]),
        }

        # write file
        with open("activity_history.json", "w") as outfile:
            json.dump(activity_history, outfile)


def get_time():
    global hs
    # time functions
    now = datetime.now()
    hs["now"] = round(datetime.timestamp(now))
    hs["time"] = str(now.strftime("%H:%M %D"))


# functions
def nice_date(time):
    timestamp = datetime.fromtimestamp(time)
    return timestamp.strftime("%H:%M %d/%b").upper()


def nice_hotspot_name(name):
    if not bool(config["name"]):
        config["name"] = name.replace("-", " ").upper()
    return config["name"]


def nice_hotspot_initials(name):
    if not bool(config["initials"]):
        name = nice_hotspot_name(name)
        config["initials"] = "".join(item[0].upper() for item in name.split())
    return config["initials"]


def nice_hnt_amount_or_seconds(amt):
    niceNum = 0.00000001
    niceNumSmall = 100000000

    if isinstance(amt, float):
        # float. for time i
        amt_output = "{:.2f}".format(amt)
    else:
        # int. up to 3 decimal payments
        amt_output = "{:.3f}".format(amt * niceNum)

    # int. 8 decimal places for micropayments
    # if amt > 0 and amt < 100000 :
    if amt in range(0, 100000):
        amt_output = "{:.8f}".format(amt / niceNumSmall).rstrip("0")
        amt_output = f"`{amt_output}`"

    return str(amt_output)


# invalid reason nice name, or raw reason if not in dict
def nice_invalid_reason(ir):
    return (
        invalid_reason_short_names[ir] if ir in invalid_reason_short_names else str(ir)
    )


###activity type name to short name
def reward_short_name(reward_type):
    return (
        reward_short_names[reward_type]
        if reward_type in reward_short_names
        else reward_type.upper()
    )


def load_activity_data():
    global activities, config, hs, wellness_check, send, send_report, send_wellness_check

    # try to get json or return error
    status = ""
    try:
        # LIVE API data
        activity_endpoint = (
            helium_api_endpoint + "hotspots/" + config["hotspot"] + "/activity/"
        )
        activity_request = requests.get(activity_endpoint)
        data = activity_request.json()

        ### DEV Only
        ###LOCAL load data.json
        # with open("data.json") as json_data_file:
        #  data = json.load(json_data_file)

    except requests.RequestException:
        status = "Connectivity"
    except ValueError:  # includes simplejson.decoder.JSONDecodeError
        status = "Parsing JSON"
    except (IndexError, KeyError):
        status = "JSON format"

    if bool(status):
        print(f"\n{hs['time']} Activity API Error: {status}")
        quit()

    # quit if no data
    if "data" not in data:
        print(f"\n{hs['time']} Activity API: Bad Data")
        quit()

    # set wellness_check if last.send exists
    if "last" in config and "send" in config["last"]:
        wellness_check = int(config["last"]["send"] + wellness_check_seconds)

    # add/update cursor to config
    if "cursor" not in config:
        config["cursor"] = ""
    if config["cursor"] != data["cursor"]:
        config["cursor"] = data["cursor"]

    # only send if send history. not for new users
    if "send" in config["last"] and hs["now"] >= wellness_check:
        print(
            f"\n{hs['time']} Wellness Check, {wellness_check_hours}hrs, No New Activities",
            end="",
        )
        send = send_wellness_check = send_report = True

    # no data or send_report false
    elif not data["data"] and not bool(send_report):
        # print(f"{hs['time']} no activities")
        print(".", end="")
        quit()

    # set activities, set last.send, update config
    else:
        send = True
        activities = data["data"]


###activity type poc_receipts_v1
def poc_receipts_v1(activity):
    valid_text = "💩  Invalid"
    time = nice_date(activity["time"])

    txn_link = helium_explorer_tx + activity["hash"]

    witnesses = {}
    wit_count = 0
    if "path" in activity and "witnesses" in activity["path"][0]:
        witnesses = activity["path"][0]["witnesses"]
        wit_count = len(witnesses)
    # pluralize Witness
    wit_plural = "es" if wit_count != 1 else ""
    wit_text = f"{wit_count} Witness{wit_plural}"

    # challenge accepted
    if "challenger" in activity and activity["challenger"] == config["hotspot"]:
        output_message.append(
            f"🏁 ...Challenged Beaconer, {wit_text}  `{time}` [🔍]({txn_link})"
        )

    # beacon sent
    elif (
        "challengee" in activity["path"][0]
        and activity["path"][0]["challengee"] == config["hotspot"]
    ):

        # beacon sent plus witness count and valid count
        valid_wit_count = 0
        for wit in witnesses:
            if bool(wit["is_valid"]):
                valid_wit_count = valid_wit_count + 1
        msg = f"🌋 Sent Beacon, {wit_text}"
        if bool(wit_count):
            if valid_wit_count == len(witnesses):
                valid_wit_count = "All"
            msg += f", {valid_wit_count} Valid"
        msg += f"  `{time}` [🔍]({txn_link})"

        output_message.append(msg)

    # witnessed beacon plus valid or invalid and invalid reason
    elif bool(witnesses):
        vw = 0  # valid witnesses
        valid_witness = False
        for w in witnesses:

            # valid witness count among witnesses
            if "is_valid" in w and bool(w["is_valid"]):
                vw = vw + 1

            if w["gateway"] == config["hotspot"]:
                witness_info = ""
                if bool(w["is_valid"]):
                    valid_witness = True
                    valid_text = "🛸 Valid"  # 🤙
                    witness_info = f", 1 of {wit_count}"
                elif "invalid_reason" in w:
                    valid_text = "💩 Invalid"
                    witness_info = ", " + nice_invalid_reason(w["invalid_reason"])

        # add valid witness count among witnesses
        if bool(valid_witness) and vw >= 1:
            vw = "All" if vw == len(witnesses) else vw
            witness_info += f", {vw} Valid"

        output_message.append(
            f"{valid_text} Witness{witness_info}  `{time}` [🔍]({txn_link})"
        )

    # other
    else:
        ac_type = activity["type"]
        output_message.append(
            f"🏁 poc_receipts_v1 - {ac_type.upper()}  `{time}` [🔍]({txn_link})"
        )


def loop_activities():
    global send_report, history_repeats

    if bool(activities):  # and not bool(send_report):

        # load history
        load_activity_history()

        for activity in activities:

            # skip if activity is in history
            if activity["hash"] in activity_history:  # and not bool(send_report):
                history_repeats = history_repeats + 1
                continue  # skip this element, continue for-loop

            # save activity hash if not found
            else:
                activity_history.append(activity["hash"])

            # activity time
            time = nice_date(activity["time"])

            # reward
            if activity["type"] == "rewards_v2":
                for reward in activity["rewards"]:
                    rew = reward_short_name(reward["type"])
                    amt = nice_hnt_amount_or_seconds(reward["amount"])
                    output_message.append(
                        f"🍪 Reward 🥓{amt}, {rew}  `{time}` [🔍]({txn_link})"
                    )
            # transferred data
            elif activity["type"] == "state_channel_close_v1":
                for summary in activity["state_channel"]["summaries"]:
                    packet_plural = "s" if summary["num_packets"] != 1 else ""
                    output_message.append(
                        f"🚛 Transferred {summary['num_packets']} Packet{packet_plural} ({summary['num_dcs']} DC)  `{time}` [🔍]({txn_link})"
                    )

            # ...challenge accepted
            elif activity["type"] == "poc_request_v1":
                output_message.append(
                    f"🎲 Created Challenge...  `{time}` [🔍]({txn_link})"
                )

            # beacon sent, valid witness, invalid witness
            elif activity["type"] == "poc_receipts_v1":
                poc_receipts_v1(activity)

            # other
            else:
                other_type = activity["type"]
                output_message.append(
                    f"🚀 {other_type.upper()}  `{time}` [🔍]({txn_link})"
                )


def load_hotspot_data_and_status():
    ###hotspot data
    global hs, config, add_welcome, send_wellness_check
    new_balance = new_reward_scale = new_block_height = new_status = ""

    # try to get json or return error
    status = ""
    try:
        hs_endpoint = helium_api_endpoint + "hotspots/" + config["hotspot"]
        hs_request = requests.get(hs_endpoint)
        data = hs_request.json()
        if not data["data"]:
            print(f"no hotspot data {hs['time']}")
            quit()
        else:
            hotspot_data = data["data"]
        del hs_request
    except requests.RequestException:
        status = "Connectivity"
    except ValueError:  # includes simplejson.decoder.JSONDecodeError
        status = "Parsing JSON"
    except (IndexError, KeyError):
        status = "JSON format"

    if bool(status):
        print(f"\n{hs['time']} Hotspot API Error: {status}")
        quit()

    # quit if no data
    if "data" not in data:
        print(f"\n{hs['time']} Helium Hotspot API. No 'data' key in Response")
        quit()

    ### hotspot data
    hs_add = {
        "owner": hotspot_data["owner"],
        "name": nice_hotspot_name(hotspot_data["name"]),
        "initials": nice_hotspot_initials(hotspot_data["name"]),
        "status": str(hotspot_data["status"]["online"]).upper(),
        "height": hotspot_data["status"]["height"],
        "block": hotspot_data["block"],
        "reward_scale": "{:.2f}".format(round(hotspot_data["reward_scale"], 2)),
    }
    hs.update(hs_add)
    del data, hotspot_data, hs_add

    # add/update cursor to config. supports hotspot ownership transfers
    if "owner" not in config or config["owner"] != hs["owner"]:
        config["owner"] = hs["owner"]

    ###block height percentage
    hs["block_height"] = round(hs["height"] / hs["block"] * 100, 2)
    hs["block_height"] = (
        "*NSYNC" if hs["block_height"] > 98 else str(hs["block_height"]) + "%"
    )

    if "block_height" not in config["last"]:
        config["last"]["block_height"] = "0"
    ###add to config if new
    if hs["block_height"] != config["last"]["block_height"]:
        new_block_height = True
        config["last"]["block_height"] = hs["block_height"]

    ###wallet data
    wallet_request = requests.get(helium_api_endpoint + "accounts/" + hs["owner"])
    w = wallet_request.json()
    hs["balance"] = nice_hnt_amount_or_seconds(w["data"]["balance"])
    if "balance" not in config["last"]:
        config["last"]["balance"] = "0"
    ###add to config if new
    if hs["balance"] != config["last"]["balance"]:
        new_balance = True
        config["last"]["balance"] = hs["balance"]
    del wallet_request, w

    ### reward_scale
    if "reward_scale" not in config["last"]:
        config["last"]["reward_scale"] = "0"
    ###add to config if new
    if hs["reward_scale"] != config["last"]["reward_scale"]:
        new_reward_scale = True
        config["last"]["reward_scale"] = hs["reward_scale"]

    ### status
    if "status" not in config["last"]:
        config["last"]["status"] = ""
    ###add to config if new
    if hs["status"] != config["last"]["status"]:
        new_status = True
        config["last"]["status"] = hs["status"]

    #### STYLED status text
    ### bold balance if has changed
    balance_styled = "**" + hs["balance"] + "**" if bool(new_balance) else hs["balance"]
    ### bold reward_scale if has changed
    reward_scale_styled = (
        "**" + hs["reward_scale"] + "**"
        if bool(new_reward_scale)
        else hs["reward_scale"]
    )
    ### bold block_height if has changed
    block_height_styled = (
        "**" + hs["block_height"] + "**"
        if bool(new_block_height)
        else hs["block_height"]
    )
    ### bold status if not 'online'
    status_styled = "**" + hs["status"] + "**" if bool(new_status) else hs["status"]

    # default status msg
    status_msg = (
        "📡 **"
        + hs["initials"]
        + "** 🔥"
        + status_styled
        + " 🥑"
        + block_height_styled
        + " 🍕"
        + reward_scale_styled
        + " 🥓"
        + balance_styled
    )

    # insert to top of output_message
    output_message.insert(0, status_msg)

    # add in wellness check message. not if new
    # if not bool(add_welcome) and bool(send_wellness_check):
    if (
        not bool(add_welcome)
        and bool(send_wellness_check)
        and "send" in config["last"]
        and bool(config["last"]["send"])
    ):
        hour_plural = "s" if wellness_check_hours != 1 else ""
        lapse_msg = (
            f"`🚧 No API Activities in the Last {wellness_check_hours}hr{hour_plural} `"
        )
        output_message.insert(0, lapse_msg)


def discord_send():
    global send, add_welcome, send_report, output_message_length

    # send if no last.send in config
    if "last" in config and "send" not in config["last"]:
        send = add_welcome = True

    # send if more than 1 (default) msg
    elif len(output_message) > 1:
        send = True

    # unless send report, don't send, repeats only
    elif not bool(send_report):
        send = False
        print(":", end="")  # print(f"{hs['time']} repeat activities")
        quit()

    # add welcome msg to output if no config[last][send]
    if bool(add_welcome):
        output_message.insert(0, f"🤙 **{hs['name']}  [ 📡 {hs['initials']} ]**")
        print(f"\n{hs['time']} Welcome msg added", end="")

    if bool(send):
        # only send activity, remove status if recently sent. keep if report
        if (
            "last" in config
            and "send" in config["last"]
            and hs["now"] < (config["last"]["send"] + interval_pop_status_seconds)
        ):
            output_message.pop(0)

        # update last.send to be last status sent
        config["last"]["send"] = hs["now"]
        config["last"]["send_nice"] = nice_date(config["last"]["send"])

        output_message_length = len(output_message)

        discord_message = "\n".join(output_message)

        ### Dev only
        # print(discord_message)
        # exit()

        webhook = DiscordWebhook(url=config["discord_webhook"], content=discord_message)
        # send
        webhook_response = webhook.execute()
        return webhook_response.reason


#########################
### main
def main():

    # time_execution
    time_execution_t0 = time.time()

    get_time()
    load_config()
    load_activity_data()

    # if activity data...
    load_hotspot_data_and_status()
    loop_activities()

    # if bobcat set in config
    local_bobcat_miner_report()

    # send
    discord_response_reason = discord_send()

    # write history
    update_activity_history()

    # write config
    update_config()

    # time_execution end
    time_execution_t1 = time.time()
    time_execution_seconds = nice_hnt_amount_or_seconds(
        time_execution_t1 - time_execution_t0
    )

    # cron log
    print(
        f"\n{hs['time']} a:{str(len(activities))} r:{str(history_repeats)} m:{str(output_message_length)} discord:{discord_response_reason} sec:{time_execution_seconds}"
    )


### execute main() if main is first module
if __name__ == "__main__":
    main()
