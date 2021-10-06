# syntax=docker/dockerfile:1
FROM python:3.9-slim-buster


ENV VIRTUAL_ENV=hds_env \
    PATH="$VIRTUAL_ENV/bin:$PATH"
RUN apt-get update; \
    apt-get install -y git cron; \
    git clone -b v.04 https://github.com/co8/hds.git; \
    python3 -m venv $VIRTUAL_ENV; \
    . "$VIRTUAL_ENV"/bin/activate;
WORKDIR hds
RUN pip3 install -r requirements.txt; \
    cp new-config.json config.json; \
    cp new-activity_history.json activity_history.json; \
    cp hds-cron.txt /etc/cron.d/crontab; \
    chmod 0644 /etc/cron.d/crontab; \
    /usr/bin/crontab /etc/cron.d/crontab

#ENV HOTSPOT=
#ENV DISCORD_WEBHOOK=
#ENV BOBCAT_LOCAL_ENDPOINT=


# Save ENV - HOTSPOT, DISCORD_WEBHOOK, BOBCAT_LOCAL_ENDPOINT into config

CMD ["python", "hds.py"]
#CMD ["crontab", "-l"]