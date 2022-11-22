FROM ubuntu:22.04

ENV DEBIAN_FRONTEND="noninteractive"


## installing Python 3.8 
## (Note: Comment this section if you use python official image as base image)
RUN apt-get update && \
	apt-get install -y software-properties-common wget curl htop build-essential && \
	add-apt-repository ppa:deadsnakes/ppa && \
	apt-get update && \
	apt-get install -y python3.8 python3.8-dev python3-pip python3.8-distutils && \
	ln -s /usr/bin/python3.8 /usr/bin/python && \
	curl https://bootstrap.pypa.io/get-pip.py | python && \
	pip install --upgrade pip && \
	apt-get purge -y --auto-remove build-essential python3.8-dev && \
	apt-get clean && \
	rm -rf /var/lib/apt/lists/*
## Done with python installation

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

RUN pip install --no-cache-dir  python-telegram-bot[all] --pre
RUN pip install --no-cache-dir  mongoengine \
								flask \
								six \
								asgiref