#!/bin/bash

python3 env_to_config.py HOTSPOT=$HOTSPOT DISCORD_WEBHOOK=$DISCORD_WEBHOOK BOBCAT_LOCAL_ENDPOINT=$BOBCAT_LOCAL_ENDPOINT

sleep 5

python3 hds.py

cron -f
