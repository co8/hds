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
- Run every 5 minutes and at Reboot
- Change directory path to match your own 

    $ crontab -e
    */2 * * * * cd ~/hds; python3 hds.py  >> ~/cron.log 2>&1
    @reboot ~/hds; python3 hds.py  >> ~/cron.log 2>&1

Run directly from the directory

    cd ~/hds/
    python3 hds.py

End with an example of getting some data out of the system or using it
for a little demo


## Deployment

Add additional notes to deploy this on a live system

## Authors

  - **Enrique R Grullon** - *Developer* -
    [co8](https://github.com/co8)
