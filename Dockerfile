# syntax=docker/dockerfile:1
FROM python:3.9-slim-bullseye

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN apt-get update; \
    apt-get install -y git cron virtualenv; \
    mkdir /hds; \
    cd /hds; \
    git clone https://github.com/co8/hds.git

WORKDIR /hds
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY new-config.json config.json
COPY new-activitiy_history.json activitiy_history.json
COPY hds-cron /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab \
    /usr/bin/crontab /etc/cron.d/crontab

COPY hds.py .
CMD ["python", "hds.py"]