# Keeper Benchmark

This respository offers an easy way to benchmark the performance of ClickHouse Keeper versus Zookeeper.


Info table
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
    `keeper_jvm_memory` String,
    `exception` String,
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
    `properties` Map(String, String)
)
ENGINE = SharedMergeTree('/clickhouse/tables/{uuid}/{shard}', '{replica}')
ORDER BY (experiment_id, benchmark_id)
SETTINGS index_granularity = 8192
```


Metric table
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