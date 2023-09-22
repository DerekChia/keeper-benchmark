python3 clickhouse-docker-cluster/docker-compose.py --cluster-directory cluster_1 --action clean
python3 clickhouse-docker-cluster/generate.py --cluster-directory cluster_1 --shard 0 --replica 0 --keeper-type "chkeeper" --keeper-count 3 --keeper-cpu 1 --keeper-memory "2048m" --keeper-jvm-memory "1843m"
python3 clickhouse-docker-cluster/docker-compose.py --cluster-directory cluster_1 --action up
sleep 5

python3 keeper-bench-benchmarking/benchmark.py --keeper-type "chkeeper" --keeper-count 3 --keeper-cpu 1 --keeper-memory "2048m" --keeper-jvm-memory "1843m" --host-info "m6a.24xlarge" --config-concurrency 500 --config-iterations 1280000 --workload-file "multi_write_70_pct.yaml.jinja" --no-keeper-prometheus-metric
python3 clickhouse-docker-cluster/docker-compose.py --cluster-directory cluster_1 --action clean
sleep 5

# --no-keeper-prometheus-metric

# multi_write_70_pct.yaml.jinja
# multi_write_only.yaml.jinja
# millions_of_znodes.yaml.jinja

