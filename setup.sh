#!/bin/bash

sudo apt update && sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y

# docker
sudo su
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

sudo usermod -aG docker ubuntu

# docker-compose
DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
mkdir -p $DOCKER_CONFIG/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.20.3/docker-compose-linux-x86_64 -o $DOCKER_CONFIG/cli-plugins/docker-compose
chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose

# Python environment
sudo DEBIAN_FRONTEND=noninteractive apt install python3-pip python3-venv -y
python3 -m venv venv
source venv/bin/activate
pip install -U clickhouse_connect==0.6.12 Jinja2 docker requests python-dotenv pandas==2.1 pyyaml
