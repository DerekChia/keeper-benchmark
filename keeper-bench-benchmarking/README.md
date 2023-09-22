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


```JSON
{
    "timestamp": 1689615527391,
    "read_results":
    {
        "total_requests": 20000,
        "requests_per_second": 1563.6149998846627,
        "bytes_per_second": 694289.6229762869,
        "percentiles":
        [
            {
                "0.00": 0.267
            },
            {
                "10.00": 76.002
            },
            {
                "20.00": 106.63
            },
            {
                "30.00": 137.21
            },
            {
                "40.00": 168.844
            },
            {
                "50.00": 194.132
            },
            {
                "60.00": 216.125
            },
            {
                "70.00": 253.33
            },
            {
                "80.00": 300.003
            },
            {
                "90.00": 361.239
            },
            {
                "95.00": 408.319
            },
            {
                "99.00": 486.683
            },
            {
                "99.90": 583.344
            },
            {
                "99.99": 590.518
            }
        ]
    },
    "write_results":
    {
        "total_requests": 20000,
        "requests_per_second": 1534.1852441857059,
        "bytes_per_second": 52488492.012958507,
        "percentiles":
        [
            {
                "0.00": 13.549
            },
            {
                "10.00": 80.603
            },
            {
                "20.00": 112.62
            },
            {
                "30.00": 143.532
            },
            {
                "40.00": 172.671
            },
            {
                "50.00": 196.405
            },
            {
                "60.00": 219.185
            },
            {
                "70.00": 257.178
            },
            {
                "80.00": 303.858
            },
            {
                "90.00": 362.742
            },
            {
                "95.00": 407.702
            },
            {
                "99.00": 493.835
            },
            {
                "99.90": 585.894
            },
            {
                "99.99": 590.603
            }
        ]
    }
}
```

python3 clickhouse-docker-cluster/generate.py --cluster-directory cluster_1 --shard 0 --replica 0 --keeper-type "zookeeper" --keeper-count 3 --cpu-keeper 1 --memory-keeper "1024m"
python3 clickhouse-docker-cluster/docker-compose.py --cluster-directory cluster_1 --action clean
python3 clickhouse-docker-cluster/docker-compose.py --cluster-directory cluster_1 --action up
sleep 10
python3 keeper-bench-benchmarking/benchmark.py --keeper-type "zookeeper" --keeper-count 3 --cpu-keeper 1 --memory-keeper "1024m" --host-info "m6a.4xlarge" --config_concurrency 10 --config_iterations 10000 --config_multi 1