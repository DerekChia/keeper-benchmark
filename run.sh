for NUM_REPEAT in {1..10}
do
    for CONFIG_CONCURRENCY in 3 10 100 500
    do
        for CONFIG_ITERATIONS in 10000 160000 1280000 6400000
        do
            for CPU_MEMORY_JVM in "1 2048m 1024m" "3 2048m 1024m" "6 6144m 3072m" "16 6144m 3072m"
            do
                for KEEPER_TYPE in "zookeeper" "chkeeper"
                do
                    set -- $CPU_MEMORY_JVM
                    python3 clickhouse-docker-cluster/generate.py --cluster-directory cluster_1 --shard 0 --replica 0 --keeper-type $KEEPER_TYPE --keeper-count 3 --keeper-cpu $1 --keeper-memory $2
                    python3 clickhouse-docker-cluster/docker-compose.py --cluster-directory cluster_1 --action clean
                    python3 clickhouse-docker-cluster/docker-compose.py --cluster-directory cluster_1 --action up
                    sleep 5
                    python3 keeper-bench-benchmarking/benchmark.py --keeper-type $KEEPER_TYPE --keeper-count 3 --keeper-cpu $1 --keeper-memory $2 --keeper-jvm-memory $3 --host-info "m6a.24xlarge" --config-concurrency $CONFIG_CONCURRENCY --config-iterations $CONFIG_ITERATIONS --keeper-bench-workload-file "multi_write_70_pct.yaml.jinja" --no-keeper-prometheus-metric
                    python3 clickhouse-docker-cluster/docker-compose.py --cluster-directory cluster_1 --action clean
                    sleep 5
                done
            done
        done
    done
done

