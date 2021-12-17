# syntax=docker/dockerfile:1

# install python
FROM python:3.9-slim-buster
USER root

# set empty config vars and virtual env name
ENV HOTSPOT="" \
    DISCORD_WEBHOOK="" \
    BOBCAT_LOCAL_ENDPOINT="" \
    WELLNESS_CHECK_HOURS="8" \
    VIRTUAL_ENV=/opt/venv \
    PATH="$VIRTUAL_ENV/bin:$PATH"

# APT, git clone HDS, Start V-Env
RUN python3 -m venv $VIRTUAL_ENV

RUN apt-get update; \
    apt-get install -y git cron;

RUN git clone -b v.04 https://github.com/ryanho87/hds.git

WORKDIR /hds

RUN pip3 install -r requirements.txt

RUN cp new-activity_history.json activity_history.json; \
    cp new-config.json config.json

RUN cp crontab-docker /etc/cron.d/hds-crontab; \
    chmod 0644 /etc/cron.d/hds-crontab; \
    crontab-docker /etc/cron.d/hds-crontab

ADD start.sh /hds
ADD env_to_config.py /hds

CMD ./start.sh