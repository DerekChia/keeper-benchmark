from pathlib import Path
import argparse
import os


def up(cluster_directory):
    """
    Start cluster
    """
    os.system(f"docker compose -f {cluster_directory}/docker-compose.yml up -d")


def clean():
    """
    Remove all containers and volumes
    """
    os.system("docker ps -aq | xargs docker stop | xargs docker rm")
    os.system("docker volume prune -a -f")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cluster-directory", type=str, default="cluster_1")
    parser.add_argument("--action", type=str)
    args = parser.parse_args()

    if args.action == "up":
        up(args.cluster_directory)
    elif args.action == "clean":
        clean()
