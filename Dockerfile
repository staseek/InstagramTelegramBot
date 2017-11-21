FROM ubuntu:latest
MAINTAINER stasyatr
RUN apt update -y
RUN apt upgrade -y
RUN apt install -y python3 python3-pip
RUN apt install -y libsqlcipher-dev
COPY . /InstagramoBot
WORKDIR /InstagramoBot
RUN pip3 install -r requirements.txt
CMD ["python3", "InstagramoBot.py"]