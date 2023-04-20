FROM tiangolo/meinheld-gunicorn-flask:python3.8-alpine3.11

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./lingraph/ /app

ENV MODULE_NAME=app
