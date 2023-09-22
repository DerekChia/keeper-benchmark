# import os
# from omegaconf import DictConfig, OmegaConf
# import hydra

# @hydra.main(version_base=None, config_path=".", config_name="config")
# def my_app(cfg):
#     print(OmegaConf.to_yaml(cfg))

# if __name__ == "__main__":
#     my_app()

# args = {
#     'cluster_directory': 'cluster_1', 
#     'shard': 0, 
#     'replica': 0, 
#     'keeper_type': 'chkeeper', 
#     'keeper_count': 3, 
#     'keeper_cpu': 1,
#     'keeper_memory': '2048m',
#     'keeper_jvm_memory': '1843m' # ignored for chkeeper
# }


########################################
##### Part 0 - get config
########################################
import yaml
import argparse
from pathlib import Path

with open(Path(__file__).resolve().parent /'config.yaml', 'r') as file:
    f = yaml.safe_load(file)

print(f)

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
x['keeper_memory'] = '2048m'
x['keeper_jvm_memory'] = '1843m'
x['native_protocol_port'] = 9000
x['http_api_port'] = 8123
x['ch_prometheus_port'] = 9363
x['keeper_raft_port'] = 9234
x['keeper_internal_replication'] = 'true'
x['chnode_prefix'] = 'chnode'
x['cluster_name'] = 'default'
x['jinja_template_directory'] = 'default'

# values depend on keeper_type
if x['keeper_type'] == "chkeeper":
    x['keeper_prefix'] = "chkeeper"
    x['keeper_port'] = 9181
    x['keeper_version'] = "23.8"
    x['keeper_prometheus_port'] = 9363
elif x['keeper_type'] == "zookeeper":
    x['keeper_prefix'] = "zookeeper"
    x['keeper_port'] = 2181
    x['keeper_version'] = "3.8"
    x['keeper_prometheus_port'] = 7000

# args = argparse.Namespace()
# args.cluster_directory = 'cluster_1'
# args.shard = 0
# args.replica = 0
# args.keeper_type = 'zookeeper'
# args.keeper_count = 3 
# args.keeper_cpu = 1
# args.keeper_memory = '2048m'
# args.keeper_jvm_memory = '1843m' # ignored for chkeeper

# args.native_protocol_port = 9000
# args.http_api_port = 8123
# args.ch_prometheus_port = 9363
# args.keeper_raft_port = 9234
# args.keeper_internal_replication = 'true'

# args.chnode_prefix = 'chnode'
# args.cluster_name = 'default'
# args.jinja_template_directory = 'default'

# setattr(
#     args,
#     "cluster_directory",
#     str(Path(__file__).resolve().parent / args.cluster_directory),
# )

# # values depend on keeper_type
# if args.keeper_type == "chkeeper":
#     setattr(args, "keeper_prefix", "chkeeper")
#     setattr(args, "keeper_port", 9181)
#     setattr(args, "keeper_version", "23.8")
#     setattr(args, "keeper_prometheus_port", 9363)
# elif args.keeper_type == "zookeeper":
#     setattr(args, "keeper_prefix", "zookeeper")
#     setattr(args, "keeper_port", 2181)
#     setattr(args, "keeper_version", "3.8")
#     setattr(args, "keeper_prometheus_port", 7000)

docker_compose.clean()
generate.generate_cluster(x)
docker_compose.up(cluster_directory=Path(__file__).resolve().parent / 'cluster_1')

# ########################################
# ##### pause for cluster to be ready
# ########################################
# import time
# time.sleep(5)

# ########################################
# ##### Part 2 - benchmarking
# ########################################

# from benchmark import start
# args = argparse.Namespace()
# args.keeper_type = 'zookeeper'
# args.keeper_count = 3
# args.keeper_cpu = 1
# args.keeper_memory = '2048m'
# args.keeper_jvm_memory = '1843m' # ignored for chkeeper
# args.host_info = 'm6a.24xlarge'
# args.config_concurrency = 500
# args.config_iterations = 6400000
# args.workload_file = 'multi_write_70_pct.yaml.jinja'
# args.no_keeper_prometheus_metric = False

# start(args)
# docker_compose.clean()