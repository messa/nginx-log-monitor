FROM python:3.8-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

COPY requirements.txt /src/

RUN pip install wheel
RUN pip install -r /src/requirements.txt

COPY setup.py LICENSE /src/
COPY nginx_log_monitor /src/nginx_log_monitor
RUN pip install /src/

ENTRYPOINT ["nginx-log-monitor"]



