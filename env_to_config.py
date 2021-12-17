#!/usr/bin/python3

############################
# ENV TO CONFIG
# https://github.com/co8/hds
#
# Grab Docker ENV variables for HDS and convert config values to save to config.json JSON file
#
# co8.com
# enrique r grullon
# e@co8.com
# discord: co8#1934
############################

# modules/libraries
import sys
import requests
import json

# USAGE
# $ python3 env_to_config.py HOTSPOT="112MWdscG3Dj" DISCORD_WEBHOOK="https://disord/webhook/url" BOBCAT_LOCAL_ENDPOINT="https://192.168.0.100"


# define config file
config_file = "config.json"
config = {}


def load_config():
    global config
    with open(config_file) as json_data_file:
        config = json.load(json_data_file)


# Load ENVs as arguments passed to this script
# Add all ENV variables to json
def add_env_to_config():
    global config
    args = sys.argv[1:]
    for a in args:
        var = a.split("=")
        key = var[0].lower()
        config[key] = var[1]


# Update config.json file
def update_config():
    global config
    with open(config_file, "w") as outfile:
        json.dump(config, outfile)


def main():
    load_config()
    add_env_to_config()
    update_config()


# Run Script
if __name__ == "__main__":
    main()
