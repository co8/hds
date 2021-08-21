# hds

## **Hotspot Discord Status** for the Helium Network Hotspots

## Getting Started

These instructions will give you a copy of the project up and running on
your local machine for development and testing purposes. See deployment
for notes on deploying the project on a live system.

### Prerequisites

Requirements for the software and other tools to build, test and push

- [Python v3.9+ Installed](https://www.example.com)
- [How to Use Crontab](https://www.geeksforgeeks.org/crontab-in-linux-with-examples/)
- [Discord Webhook for Python](https://pypi.org/project/discordwebhook/)

### Installing

A step by step series of examples that tell you how to get a development
environment running

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

Crontab

- Run every minute and at Reboot
- If changed, update directory path to match your own
- Delete log file every Sunday at 0:00

  crontab -e
```
  */1 * * * * cd ~/hds; python3 hds.py >> cron.log 2>&1

  @reboot ~/hds; python3 hds.py >> cron.log 2>&1

  0 0 * * 0 rm cron.log
```
Run directly from the directory

    cd ~/hds/
    python3 hds.py

Command line Arguments

```py
python3 hds.py report
```

- send a bobcat miner report, if bobcat_local_endpoint is set
  
```py
python3 hds.py reset
```
- resets by setting last sent and activity history


## Support this Project

Fork this project and submit pull requests

If you find this project useful please consider supporting it

HNT: [14hriz8pmxm51FGmk1nuijHz6ng9z9McfJZgsg4yxzF2H7No3mH](https://explorer.helium.com/accounts/14hriz8pmxm51FGmk1nuijHz6ng9z9McfJZgsg4yxzF2H7No3mH)

### Seeking Grants and Bounties to Support this Project

I'm seeking grants and bounties to extend compatibility to more hotspots and continued development of this project. [e@co8.com](mailto:e@co8.com)

### Optional Hardware
For convenience, I run this script on a Raspberry Pi Zero W

[**Raspberry Pi Zero W** Kit (Amazon US)](https://amzn.to/3jWaUpF)