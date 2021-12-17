#!/bin/bash

declare -p | grep -Ev 'BASHOPTS|BASH_VERSINFO|EUID|PPID|SHELLOPTS|UID' > /container.env

# Setup a cron schedule
echo "SHELL=/bin/bash"
BASH_ENV=/container.env
# install crons
echo */1 * * * * cd /hds; /usr/local/bin/python3 hds.py >> cron.log 2>&1
> scheduler.txt
echo 20 4 * * 1 cd /hds; rm cron.log;  echo 'Cron Log Cleared\n'  >> cron.log 2>&1
> scheduler.txt

crontab scheduler.txt

# add environment variables to the config
python3 env_to_config.py HOTSPOT=$HOTSPOT DISCORD_WEBHOOK=$DISCORD_WEBHOOK BOBCAT_LOCAL_ENDPOINT=$BOBCAT_LOCAL_ENDPOINT

sleep 2

# run once to send welcome message and complete config
python3 hds.py

sleep 2

# start the cron
cron -f
