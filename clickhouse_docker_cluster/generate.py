import argparse
from pathlib import Path
from pprint import pprint
from .cluster import Cluster

def generate_cluster(args):
    # create cluster
    c = Cluster(args)
    c.prepare()
    c.generate_obj()
    c.generate_docker_compose()
    c.generate_config()

if __name__ == "__main__":
    """
    Different configurations:
    -
    """
    parser = argparse.ArgumentParser()

    # general
    parser.add_argument(
        "--ch-version", type=str, default="23.5", help="ClickHouse version"
    )
    parser.add_argument("--shard", type=int, default=1, help="Number of shard")
    parser.add_argument("--replica", type=int, default=3, help="Number of replica")
    parser.add_argument(
        "--cluster-directory",
        type=str,
        default="cluster_1",
    )

    # node configuration
    parser.add_argument("--cpu", type=int, default=1, help="CPUs for each node")
    parser.add_argument(
        "--memory", type=str, default="8192m", help="RAM (mb) for each node"
    )

    # keeper_type
    parser.add_argument(
        "--keeper-type",
        type=str,
        choices=["chkeeper", "zookeeper", "embedded"],
        help="chkeeper, zookeeper, embedded",
    )
    parser.add_argument(
        "--keeper-count", type=int, default=3, help="Number of Keepers (Min. 3)"
    )

    # keeper node configuration
    parser.add_argument("--keeper-cpu", type=int, default=1, help="CPUs for each node")
    parser.add_argument(
        "--keeper-memory", type=str, default="4096m", help="RAM (mb) for each node"
    )
    parser.add_argument("--keeper-jvm-memory", type=str, default="1024m", help="JVM Xms/Xmx")

    # ports
    parser.add_argument("--native-protocol-port", type=int, default=9000)
    parser.add_argument("--http-api-port", type=int, default=8123)
    parser.add_argument("--ch-prometheus-port", type=int, default=9363)
    parser.add_argument("--keeper-raft-port", type=int, default=9234)  # 9444
    parser.add_argument("--keeper-internal-replication", type=str, default="true")

    # misc.
    parser.add_argument("--chnode-prefix", type=str, default="chnode")
    parser.add_argument("--cluster-name", type=str, default="default")
    parser.add_argument("--jinja-template-directory", type=str, default="default")
    # args.cluster_name = f"cluster_{args.shard}S_{args.replica}R"

    args = parser.parse_args()

    setattr(
        args,
        "cluster_directory",
        str(Path(__file__).resolve().parent / args.cluster_directory),
    )

    # values depend on keeper_type
    if args.keeper_type == "chkeeper":
        setattr(args, "keeper_prefix", "chkeeper")
        setattr(args, "keeper_port", 9181)
        setattr(args, "keeper_version", "23.8")
        setattr(args, "keeper_prometheus_port", 9363)
    elif args.keeper_type == "zookeeper":
        setattr(args, "keeper_prefix", "zookeeper")
        setattr(args, "keeper_port", 2181)
        setattr(args, "keeper_version", "3.9")
        setattr(args, "keeper_prometheus_port", 7000)

    print(f"{args}")

    cluster(args)