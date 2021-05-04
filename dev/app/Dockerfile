# pull official base image
FROM python:3.9.2-slim-buster

# set working directory
WORKDIR /usr/src/app


# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV POETRY_VIRTUALENVS_CREATE=false

# install system dependencies
RUN apt-get update \
  && apt-get -y install netcat gcc \
  && apt-get clean

# install python dependencies
RUN pip install --upgrade pip
RUN pip install poetry==1.1.4
COPY ../../poetry.lock .
COPY ../../pyproject.toml .
RUN poetry install

# add app
COPY ../../app .


# add entrypoint.sh
COPY dev/app/entrypoint.sh .
RUN chmod +x /usr/src/app/entrypoint.sh

ENTRYPOINT ["/bin/sh",  "-c", "/usr/src/app/entrypoint.sh"]
