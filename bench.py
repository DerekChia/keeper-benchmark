# import os
# from omegaconf import DictConfig, OmegaConf
# import hydra

# @hydra.main(version_base=None, config_path=".", config_name="config")
# def my_app(cfg):
#     print(OmegaConf.to_yaml(cfg))

# if __name__ == "__main__":
#     my_app()

########################################
##### Part 0 - get config
########################################
import yaml
import argparse
from pathlib import Path

# with open(Path(__file__).resolve().parent /'config.yaml', 'r') as file:
#     f = yaml.safe_load(file)

# print(f)

########################################
##### Part 1 - create cluster
########################################
import os
from clickhouse_docker_cluster import docker_compose, generate

x = {}
x['cluster_directory'] = Path(__file__).resolve().parent / 'cluster_1'
x['shard'] = 0
x['replica'] = 0
x['keeper_type'] = 'zookeeper'
x['keeper_count'] = 3
x['keeper_cpu'] = 1
x['keeper_memory'] = '1024m'
x['native_protocol_port'] = 9000
x['http_api_port'] = 8123
# x['ch_prometheus_port'] = 9363
x['keeper_raft_port'] = 9234
# x['keeper_internal_replication'] = 'true'
x['chnode_prefix'] = 'chnode'
x['cluster_name'] = 'default'
x['jinja_template_directory'] = 'default'
x['keeper_extra_memory_percent'] = 20

# values depend on keeper_type
if x['keeper_type'] == "chkeeper":
    x['keeper_prefix'] = "chkeeper"
    x['keeper_port'] = 9181
    x['keeper_version'] = "23.8"
    x['keeper_prometheus_port'] = 9363
    x['keeper_jvm_memory'] = '0m'
elif x['keeper_type'] == "zookeeper":
    x['keeper_prefix'] = "zookeeper"
    x['keeper_port'] = 2181
    x['keeper_version'] = "3.8"
    x['keeper_prometheus_port'] = 7000
    x['keeper_jvm_memory'] = x['keeper_memory']
    x['keeper_memory'] = f"{int(int(x['keeper_memory'][:-1]) * (x['keeper_extra_memory_percent'] + 100)/100)}m" 

print(x)
docker_compose.clean()
generate.generate_cluster(x)
docker_compose.up(x['cluster_directory'])

########################################
##### pause for cluster to be ready
########################################
import time
time.sleep(5)

########################################
##### Part 2 - benchmarking
########################################

x['host_info'] = 'm6a.24xlarge'
x['config_concurrency'] = 500
x['config_iterations'] = 10000
x['workload_file'] = 'multi_write_70_pct.yaml.jinja'
x['no_keeper_prometheus_metric'] = False

from benchmark import start
args = argparse.Namespace()
args.keeper_type = x['keeper_type']
args.keeper_count = x['keeper_count']
args.keeper_cpu = x['keeper_cpu']
args.keeper_memory = x['keeper_memory']
args.keeper_jvm_memory = x['keeper_jvm_memory']
args.host_info = x['host_info']
args.config_concurrency = x['config_concurrency']
args.config_iterations = x['config_iterations']
args.workload_file = x['workload_file']
args.no_keeper_prometheus_metric = x['no_keeper_prometheus_metric']

start(args)
docker_compose.clean()