# syntax=docker/dockerfile:1

# install python
FROM python:3.9-slim-buster
USER root

# set empty config vars and virtual env name
ENV HOTSPOT="" \
    DISCORD_WEBHOOK="" \  
    BOBCAT_LOCAL_ENDPOINT="" \
    WELLNESS_CHECK_HOURS="8" \
    VIRTUAL_ENV=hds_env \
    PATH="$VIRTUAL_ENV/bin:$PATH"

# APT, git clone HDS
RUN python3 -m venv $VIRTUAL_ENV; \
    . "$VIRTUAL_ENV"/bin/activate; \
    apt-get update; \
    apt-get install -y git cron; \
    mkdir -p /app/hds; \      
    cd /app/hds; \ 
    git clone -b v.04 https://github.com/co8/hds.git;

WORKDIR /app/hds
# Start V-Env, Copy Files and Crontab, Load Crontab
RUN pip3 install -r requirements.txt; \
    cp new-config.json config.json; \
    cp new-activity_history.json activity_history.json; \
    cp crontab /etc/cron.d/crontab; \
    chmod 0644 /etc/cron.d/crontab; \
    /usr/bin/crontab /etc/cron.d/crontab

# Save ENV - HOTSPOT, DISCORD_WEBHOOK, BOBCAT_LOCAL_ENDPOINT into config
CMD python3 docker/env_to_config.py HOTSPOT=$HOTSPOT DISCORD_WEBHOOK=$DISCORD_WEBHOOK BOBCAT_LOCAL_ENDPOINT=$BOBCAT_LOCAL_ENDPOINT

CMD cat ../config.json

# Run HDS
CMD python3 hds.py