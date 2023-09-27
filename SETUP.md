# Benchmarking using keeper-bench

### For MacOS
cmake -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DENABLE_UTILS=1 -S . -B build
cmake --build build

### For Linux
sudo apt remove gcc -y
sudo apt-get install git cmake ccache python3 ninja-build nasm yasm gawk lsb-release wget software-properties-common gnupg
wget https://apt.llvm.org/llvm.sh
chmod +x llvm.sh
sudo ./llvm.sh 16
export CC=clang-16
export CXX=clang++-16
git clone --recursive https://github.com/ClickHouse/ClickHouse.git
cd ClickHouse
git checkout better-setup-for-keeper-bench
mkdir build
cmake -DENABLE_UTILS=1 -S . -B build
cmake --build build --target keeper-bench
cmake --build build  # or: `cd build; ninja`


<!-- on line 570 in utils/keeper-bench/Generator.cpp
change
    auto request = std::make_shared<ZooKeeperFilteredListRequest>();
to
    auto request = std::make_shared<ZooKeeperListRequest>(); -->

### Running keeper-bench
cd build/utils/keeper-bench

./utils/keeper-bench --config benchmark_config_file.yaml

### Defaults
Concurrency: 20
Iterations: 10000
Report delay: 1
Time limit: 300
Continue on error: 0
Printing output to stdout: 1
Result file path: output.json

###

```
CREATE TABLE default.keeper_bench_info
(
    `experiment_id` String COMMENT 'each experiment has two benchmark runs',
    `benchmark_id` String COMMENT 'each benchmark run is either on ZK or CHK',
    `host_info` String COMMENT 'info about host e.g. EC2 machine type m6a.4xlarge',
    `benchmark_ts` DateTime DEFAULT now() COMMENT 'timestamp - start of benchmark',
    `keeper_type` String COMMENT 'ZooKeeper or ClickHouse Keeper',
    `keeper_count` UInt32,
    `keeper_container_cpu` UInt32,
    `keeper_container_memory` String,
    `keeper_bench_config_concurrency` UInt32 COMMENT 'keeper-bench concurrency',
    `keeper_bench_config_iterations` UInt32 COMMENT 'keeper-bench iterations',
    `result_read_total_requests` UInt32 COMMENT 'output.read_results.total_requests',
    `result_read_requests_per_second` Float32 COMMENT 'output.read_results.requests_per_second',
    `result_read_bytes_per_second` Float32 COMMENT 'output.read_results.bytes_per_second',
    `result_read_percentiles` Array(Map(String, Float32)) COMMENT 'output.read_results.percentiles',
    `result_write_total_requests` UInt32 COMMENT 'output.write_results.total_requests',
    `result_write_requests_per_second` Float32 COMMENT 'output.write_results.requests_per_second',
    `result_write_bytes_per_second` Float32 COMMENT 'output.write_results.bytes_per_second',
    `result_write_percentiles` Array(Map(String, Float32)) COMMENT 'output.write_results.percentiles',
    `workload_file` String DEFAULT toString('multi_read_70_pct'),
    `keeper_jvm_memory` String,
    `properties` Map(String, String)
)
ENGINE = SharedMergeTree('/clickhouse/tables/{uuid}/{shard}', '{replica}')
ORDER BY (experiment_id, benchmark_id)
SETTINGS index_granularity = 8192
```

```
CREATE TABLE default.keeper_bench_metric
(
    `experiment_id` String COMMENT 'each experiment has two benchmark runs',
    `benchmark_id` String COMMENT 'each benchmark run is either on ZK or CHK',
    `container_hostname` String COMMENT 'container hostname',
    `metric` String COMMENT 'CPU or Memory',
    `value` Float32 COMMENT 'metric value',
    `prometheus_ts` DateTime64(3) COMMENT 'prometheus scrape time'
)
ENGINE = SharedMergeTree('/clickhouse/tables/{uuid}/{shard}', '{replica}')
ORDER BY (benchmark_id, container_hostname)
SETTINGS index_granularity = 8192
```


Same experiment id will have the same
- keeper_count
- keeper_container_cpu
- keeper_container_memory
- keeper_bench_config_concurrency
- keeper_bench_config_iterations
- keeper_bench_config_multi

https://clickhouse.com/docs/en/operations/server-configuration-parameters/settings#server-settings_zookeeper


python3 clickhouse-docker-cluster/generate.py --cluster-directory cluster_1 --shard 0 --replica 0 --keeper-type "zookeeper" --keeper-count 3 --cpu-keeper 1 --memory-keeper "1024m"
python3 clickhouse-docker-cluster/docker-compose.py --cluster-directory cluster_1 --action clean
python3 clickhouse-docker-cluster/docker-compose.py --cluster-directory cluster_1 --action up
sleep 10
python3 keeper-bench-benchmarking/benchmark.py --keeper-type "zookeeper" --keeper-count 3 --cpu-keeper 1 --memory-keeper "1024m" --host-info "m6a.4xlarge" --config_concurrency 10 --config_iterations 10000 --config_multi 1


```
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
```




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

