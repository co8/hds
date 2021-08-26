# HDS - **Hotspot Discord Status** for the Helium Hotspots

## **Hotspot Discord Status** for the Helium Network Hotspots

### Helium Activity and Reward updates sent to your Discord Channel

HDS monitors the Helium API for new activities and sends them to your Discord Channel. Activities are displayed with Contextual information to understand status, optimization and maintenance.

[Bobcat 300 Miner](https://www.bobcatminer.com/) owners can add their local address and receive miner reports including status, temperature and OTA firmware versions.

|         Discord Channel          |  Discord Mobile Notification   |
| :------------------------------: | :----------------------------: |
| ![](imgs/hds-discord-window.jpg) | ![](imgs/hds-notification.jpg) |

---

### Features

- a
- b
- c
- d
- e

---

---

### Notifications and Emojis

**Welcome Message**: :call_me_hand: THANKFUL COTTON CROCODILE [ :satellite: TCC ]

**Status Bar:** :satellite: TCC :fire:ONLINE :avocado:\*NSYNC :pizza:1.00 :bacon:23.534

- :satellite: Hotspot Initials
- :fire: Online Status
- :avocado: Synchronization
- :pizza: Transmission Reward Scale
- :bacon: Wallet Balance

**Proof of Coverage** with Context

- :game_die: Created Challenge... 16:57 23/AUG
- :checkered_flag: ...Challenged Beaconer, 7 Witnesses 04:22 23/AUG
- :volcano: Sent Beacon, 3 Witnesses, 2 Valid 13:29 23/AUG
- :flying_saucer: Valid Witness, 1 of 4, All Valid 12:04 23/AUG

**Invalid Witness** with Reason

- :poop: Invalid Witness, Too Close 12:12 23/AUG
- :poop: Invalid Witness, RSSI BLB 10:55 25/AUG
- :poop: Invalid Witness, RSSI, Too High 04:55 22/AUG

**Rewards**

- :cookie: Reward :bacon:0.013, Witness `04:31 23/AUG`
- :cookie: Reward :bacon:0.008, Challenger `04:31 23/AUG`
- :cookie: Reward :bacon:`0.0000032`, Data `04:48 24/AUG`
- :cookie: Reward :bacon:0.059, Beacon `01:42 24/AUG`

---

### Prerequisites

- [Python v3.9+](https://www.python.org/downloads/)
- [How to Use Crontab, or other scheduler](https://www.geeksforgeeks.org/crontab-in-linux-with-examples/)
- [Install Discord Webhook for Python via pip3](https://pypi.org/project/discordwebhook/)
- [Have a Discord Account](https://support.discord.com/hc/en-us/articles/360033931551-Getting-Started)
- [Make a Discord Channel and Webhook](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks)

---

### Installing

Option A: Download from Github

- Download Latest https://github.com/co8/hds/archive/refs/heads/master.zip
- rename/copy new-config.json to config.json
- rename/copy new-activity_history.json to activity_history.json
- edit config.json

Option B: Clone from Github

- $ git clone https://github.com/co8/hds
- cd hds
- cp new-config.json config.json
- cp new-activity_history.json activity_history.json
- nano config.json

---

#### Config File. Add your Hotspot, Discord Bot Webhook

```json
default
{
  "hotspot": "HOTSPOT_ADDRESS_HERE",
  "discord_webhook": "DISCORD_WEBHOOK_HERE"
}

example
{
  "hotspot": "112MWdscG3DjHTxdCrtuLk...",
  "discord_webhook": "https://discord.com/api/webhooks/878693306043871313/C6m7znYe..."
}

optional config values that can be customized
{
  "bobcat_local_endpoint": "http://192.168.1.120/",
  "wellness_check_hours": 8,
  "report_interval_hours": 72,
}
```

---

####Crontab

- run script every minute. log to file
- Optional:
  - run at reboot, if needed. eg: dedicated device
  - clear log file once a week at Sunday, 04:20am. write to cron.log
  - update from github nightly at 04:20am. write to cron.log

```BASH
% crontab -e

required
*/1 * * * * cd ~/hds; python3 hds.py >> cron.log 2>&1

optional
@reboot cd ~/hds; python3 hds.py >> cron.log 2>&1
20 4 * * 0 cd ~/hds; rm cron.log; echo "crontab: cleared cron.log file" >> cron.log
20 4 * * * cd ~/hds; echo "" >> cron.log; git fetch; git pull >> cron.log 2>&1
```

---

### Run directly from the directory

```BASH
cd ~/hds/
python3 hds.py
```

### Command line Arguments

```py
python3 hds.py report
python3 hds.py reset
```

- send a bobcat miner report, if bobcat_local_endpoint is set in config.json
- resets by setting last sent and activity history

---

### Support this Project

Fork this project and submit pull requests

If you find this project useful please consider supporting it

HNT: [14hriz8pmxm51FGmk1nuijHz6ng9z9McfJZgsg4yxzF2H7No3mH](https://explorer.helium.com/accounts/14hriz8pmxm51FGmk1nuijHz6ng9z9McfJZgsg4yxzF2H7No3mH)

### Seeking Grants and Bounties to Support this Project

I'm seeking grants and bounties to extend compatibility to more hotspots and continued development of this project. [e@co8.com](mailto:e@co8.com)

---

### Optional Hardware

For convenience, I run this script on a Raspberry Pi Zero W

[**Raspberry Pi Zero W** Kit (Amazon US)](https://amzn.to/3jWaUpF)
