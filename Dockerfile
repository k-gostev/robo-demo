# syntax=docker/dockerfile:1

#FROM --platform=linux/arm/v7 python:3.8-slim-buster
FROM --platform=linux/amd64 python:3.8-slim-buster

RUN apt-get update && apt-get install make

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY lib/ditto-clients ditto-clients-python
RUN cd ditto-clients-python && make install

COPY . .

CMD ["python3", "main.py"]