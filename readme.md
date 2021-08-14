# hds, hotspot discord status

Hotspot Discord Service for the Helium Network

## Getting Started

These instructions will give you a copy of the project up and running on
your local machine for development and testing purposes. See deployment
for notes on deploying the project on a live system.

### Prerequisites

Requirements for the software and other tools to build, test and push

- [Python3](https://www.example.com)
- [](https://www.example.com)

### Installing

A step by step series of examples that tell you how to get a development
environment running

Crontab

- Run every minute and at Reboot
- Change directory path to match your own

  $ crontab -e
  _/1 _ \* \* \* cd ~/hds; python3 hds.py >> ~/cron.log 2>&1
  @reboot ~/hds; python3 hds.py >> ~/cron.log 2>&1

Run directly from the directory

    cd ~/hds/
    python3 hds.py

End with an example of getting some data out of the system or using it
for a little demo

## Deployment

#command line arguments
python3 hds.py report - send a bobcat miner report, if bobcat_local_endpoint is set

python3 hds.py reset - reset by setting last.send to 0

### Support this Project Directly

If you find hds this project useful please consider supporting it
https://explorer.helium.com/accounts/14hriz8pmxm51FGmk1nuijHz6ng9z9McfJZgsg4yxzF2H7No3mH

## Seeking Grants and Bounties to Support this Project

If you find hds this project useful please consider supporting it

## Authors

- **Enrique R Grullon** - _Developer_ -
  [co8](https://github.com/co8)
