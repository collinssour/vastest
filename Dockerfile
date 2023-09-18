FROM public.ecr.aws/zeet/lambdahandler:latest

RUN yum install -y amazon-linux-extras && amazon-linux-extras install -y python3.8
RUN ln -s /usr/bin/python3.8 /usr/bin/python3 || true

RUN ln -s /usr/bin/pip3.8 /usr/bin/pip3 || true

# Create a writable directory
RUN mkdir /app/session

# Set permissions for the directory (optional)
RUN chmod 777 /app/session


WORKDIR /app

COPY . .



ARG GIT_COMMIT_SHA
ARG ZEET_ENVIRONMENT
ARG GUNICORN_CMD_ARGS
ARG PYTHONUNBUFFERED
ARG UVICORN_HOST
ARG ZEET_APP
ARG ZEET_PROJECT

RUN pip3 install -r requirements.txt
