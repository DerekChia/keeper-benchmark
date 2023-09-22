# ClickHouse Docker Cluster Generator

ClickHouse Docker Cluster Generator is a tool to 

## Getting Started
```
python generate.py --version 22.11 --shard 2 --replica 4 --keeper-mode embedded --keeper-count 3
```



```
git clone --recursive git@github.com:ClickHouse/ClickHouse.git

cd ClickHouse
mkdir build
export PATH=$(brew --prefix llvm)/bin:$PATH
export CC=$(brew --prefix llvm)/bin/clang
export CXX=$(brew --prefix llvm)/bin/clang++
cmake -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DENABLE_UTILS=1 -S . -B build
cmake --build build
```

Use `keeper-bench-mac-m1` for Mac M1, or `keeper-bench` for all others

### Default configuration
Keeper
- CPU - 1
- Memory - 4096m
- Version: CHK - 23.5, ZK - 3.8

### cAdvisor

Use this for Mac M1
```
image: gcr.io/cadvisor/cadvisor-arm64:0.99-porterdavid 
```

Use this for all others
```
image: gcr.io/cadvisor/cadvisor
```

### Setting up

```
sudo apt update && sudo apt upgrade -y

curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

sudo groupadd docker
sudo usermod -aG docker ${USER}
newgrp docker

sudo curl -SL https://github.com/docker/compose/releases/download/v2.14.2/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
sudo chmod +x /usr/bin/docker-compose

git clone https://github.com/DerekChia/clickhouse-docker-cluster

cd clickhouse-docker-cluster

python3 generate.py --shard 1 --replica 1 --keeper-count 3 --ch-version 23.5 --keeper-mode chkeeper

docker container prune -f && docker-compose down -v && docker-compose up

// docker container prune --filter "label=type=experiment" -f && docker-compose down -v && docker-compose up
```

tar cf bench.tar.gz bench
scp -i "derek-ch-aws.pem" ~/Desktop/bench.tar.gz ubuntu@44.203.225.85:/home/ubuntu/
tar -xvf bench.tar.gz

