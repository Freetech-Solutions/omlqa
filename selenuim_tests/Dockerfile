FROM python:3.10-alpine as run

RUN apk add --no-cache bash
WORKDIR /selenium_tests
COPY ./integration_tests .
COPY ./requirements.txt .
RUN pip install -r ./requirements.txt
