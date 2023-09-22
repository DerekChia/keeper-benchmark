import os
import sys
import yaml
import json
import time
import uuid
import argparse
import docker
import requests
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict
import logging

from utils import get_clickhouse_connect_client, create_keeper_bench_config, generate_keeper_bench_yaml, get_experiment_id

LOGGER_FILENAME = f"{Path(__file__).resolve().parent}/logs/log.log"
TABLE_BENCH_INFO = "keeper_bench_info"
TABLE_BENCH_METRIC = "keeper_bench_metric"

# Logging
logging.basicConfig(filename=LOGGER_FILENAME, format="%(asctime)s %(levelname)s %(message)s", filemode='a')
logFormatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)

def get_keeper_containers() -> Dict:
    """
    Only get prometheus metric for keeper containers
    Filter out containers with the name "keeper" and return {"container_id": "container_name"}
    """
    keeper_containers = {}
    for container in docker.from_env().containers.list():
        container_id = container.attrs["Id"]
        container_name = container.attrs["Name"][1:].lower()
        if any(name in container_name for name in ["keeper"]): 
            keeper_containers[container_id] = container_name
    return keeper_containers

def scrape_zk_metric():
    """
    Scrape from Keeper's prometheus
    """
    scrape_result = []
    keeper_containers = get_keeper_containers()
    
    if 'chkeeper' in list(keeper_containers.values())[0]:
        port = 19181
    else:
        port = 12181

    for container_name in keeper_containers.values():
        p = subprocess.Popen(f"echo mntr | nc localhost {port}", stdout=subprocess.PIPE, stderr=None, shell=True) 
        port += 1
        stdout, stderr = p.communicate()
        
        prometheus_ts = int(datetime.now().timestamp())*1000

        output = stdout.decode('utf-8')
        for line in output.split("\n")[:-1]:
            metric, value = line.split("\t")
            if str(value).lower() == "nan" or value is None:
                continue
            try:
                value = float(value)
                each_metric = {
                    "container_hostname": container_name,
                    "metric": metric,
                    "value": str(value),
                    "prometheus_ts": prometheus_ts,
                }
                scrape_result.append(each_metric)
            except ValueError:
                pass
    return scrape_result

def scrape_cadvisor_metric():
    """
    Scrape from cAdvisor's prometheus
    returns: List(Dict)
    """
    metric = []
    keeper_containers = get_keeper_containers()
    metrics_prometheus = requests.get("http://localhost:8081/metrics")
    lines = metrics_prometheus.text.split("\n")
    metrics = [
        "container_memory_working_set_bytes",
        "container_memory_usage_bytes",
        "container_memory_rss",
        "container_memory_failures_total",
        "container_memory_mapped_file",
        "container_memory_cache",
        "container_cpu_system_seconds_total",
        "container_cpu_user_seconds_total",
        "container_cpu_usage_seconds_total",
    ]

    scrape_result = []  # contains result from each scrape

    relevant_metrics = [
        line for line in lines if any(metric in line for metric in metrics)
    ]
    for relevant_metric in relevant_metrics:
        _ = relevant_metric.split(" ")
        if len(_) == 3:
            metric_name = _[0]
            value = _[1]
            prometheus_ts = int(_[2])

            relevant_metric_name = relevant_metric.split("{")[0]

            for key in keeper_containers.keys():
                if key in metric_name:
                    each_metric = {
                        "container_hostname": keeper_containers[key],
                        "metric": relevant_metric_name,
                        "value": value,
                        "prometheus_ts": prometheus_ts,
                    }
                    scrape_result.append(each_metric)
    return scrape_result

def benchmark(total_expected_requests: int, no_keeper_prometheus_metric: bool):
    """
    Experiment id is generated from `keeper_bench_config`
    """
    # start keeper-bench process
    p = subprocess.Popen(
        [
            f"{Path(__file__).resolve().parent}/keeper-bench",  # keeper-bench-mac-m1 / keeper-bench
            "--config",
            f"{Path(__file__).resolve().parent}/benchmark-config/benchmark.yaml",
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )

    is_cleaning = False
    is_successful = False
    exception_message = ""

    benchmark_metric_result = []
    stdout_lines = []
    scrape_time = 0
    while True:
        line = p.stdout.readline()
        if not line:
            break
        line_decoded = line.decode('utf-8')
        stdout_lines.append(line_decoded)
        print(f"{line_decoded}", end="")

        # scrape every 1 second
        if (time.time() - scrape_time) >= 1:
            each_metric_scrape = []
            scrape_cadvisor_result = scrape_cadvisor_metric()
            each_metric_scrape.extend(scrape_cadvisor_result)
            if not no_keeper_prometheus_metric:
                scrape_zk_result = scrape_zk_metric()
                each_metric_scrape.extend(scrape_zk_result)
            benchmark_metric_result.extend(each_metric_scrape)
            scrape_time = time.time()

        if any(e in line_decoded.lower() for e in ["exception", "broken"]):
            exception_message = line_decoded.strip()
            break
        elif "---- Cleaning up test data ----" in line_decoded:
            is_cleaning = True
            break

    # print("no_keeper_prometheus_metric", no_keeper_prometheus_metric)
    # print("benchmark_metric_result", benchmark_metric_result)

    keeper_bench_output = {}
    if is_cleaning:
        keeper_bench_output = json.loads(stdout_lines[-2])

        total_read_requests = keeper_bench_output['read_results']['total_requests'] if "read_results" in keeper_bench_output else 0
        total_write_requests = keeper_bench_output['write_results']['total_requests'] if "write_results" in keeper_bench_output else 0
        total_actual_requests = total_read_requests + total_write_requests

        if total_expected_requests == total_actual_requests:
            is_successful = True

    return keeper_bench_output, benchmark_metric_result, is_successful, exception_message

def save_benchmark_metric_result(benchmark_metric_result):
    """
    save_benchmark_metric_result
    """
    # for dict_ in benchmark_metric_result:
    #     if "host_info" in dict_:
    #         del dict_["host_info"]

    # data = [list(metric_data.values()) for metric_data in benchmark_metric_result]

    data = []
    for metric in benchmark_metric_result:
        # logger.info(f"{metric['metric']} {metric['value']}")
        data.append([metric['experiment_id'], metric['benchmark_id'], metric['container_hostname'], metric['metric'], metric['value'], metric['prometheus_ts']])

    client = get_clickhouse_connect_client()

    # start = 0
    # end = len(data)
    # step = 10
    # for i in range(start, end, step):
    #     x = i
    #     for _ in data[x:x+step]:
    #         logger.info(_)
    #         logger.info(f"{_[-2]}, {type(_[-2])}")
    #     logger.info(" ")
    #     client.insert(f"{TABLE_BENCH_METRIC}", data[x:x+step], column_names=["experiment_id", "benchmark_id", "container_hostname", "metric", "value", "prometheus_ts"])

    client.insert(f"{TABLE_BENCH_METRIC}", data, column_names=["experiment_id", "benchmark_id", "container_hostname", "metric", "value", "prometheus_ts"])

    # benchmark_id = str(benchmark_metric_result[0]["benchmark_id"])

    # result_memory = client.query_df(
    #     f"""select
    #             container_hostname, 
    #             formatReadableSize(avg(value)) as avg_memory, 
    #             formatReadableSize(min(value)) as min_memory, 
    #             formatReadableSize(max(value)) as max_memory, 
    #             formatReadableSize(median(value)) as median_memory 
    #         from {TABLE_BENCH_METRIC} 
    #         where metric = 'container_memory_working_set_bytes' and benchmark_id = '{benchmark_id}' 
    #         group by container_hostname 
    #         order by container_hostname
    #         """
    # )

    # print(result_memory)

    # result_cpu = client.query_df(
    #     f"""select 
    #             container_hostname, 
    #             max(value) as max_cpu 
    #         from {TABLE_BENCH_METRIC} 
    #         where metric = 'container_cpu_system_seconds_total' and benchmark_id = '{benchmark_id}' 
    #         group by container_hostname 
    #         order by container_hostname"""
    # )

    # print(result_cpu)


def save_benchmark_info_result(experiment_id: str, benchmark_id: str, benchmark_ts: int, keeper_bench_config: dict, keeper_bench_output: dict, exception_message: str) -> None:
    """
    save_benchmark_info_result
    """

    result = {
        "experiment_id": experiment_id,
        "benchmark_id": benchmark_id,
        "host_info": keeper_bench_config['host_info'],
        "benchmark_ts": benchmark_ts,
        "keeper_type": keeper_bench_config['keeper_type'],
        "keeper_count": keeper_bench_config['keeper_count'],
        "keeper_container_cpu": keeper_bench_config['keeper_cpu'],
        "keeper_container_memory": keeper_bench_config['keeper_memory'],
        "keeper_jvm_memory": keeper_bench_config['keeper_jvm_memory'],
        "exception": exception_message,
        "keeper_bench_config_concurrency": keeper_bench_config['config_concurrency'],
        "keeper_bench_config_iterations": keeper_bench_config['config_iterations'],
        "workload_file": keeper_bench_config['workload_file'],
        "properties": {"keeper_prometheus_metrics": "false"} if keeper_bench_config['no_keeper_prometheus_metric'] else {"keeper_prometheus_metrics": "true"}
    }

    if "read_results" in keeper_bench_output:
        keeper_bench_read_result = {
            "result_read_total_requests": keeper_bench_output["read_results"]["total_requests"],
            "result_read_requests_per_second": keeper_bench_output["read_results"]["requests_per_second"],
            "result_read_bytes_per_second": keeper_bench_output["read_results"]["bytes_per_second"],
            "result_read_percentiles": keeper_bench_output["read_results"]["percentiles"],
        }
        result.update(keeper_bench_read_result)

    if "write_results" in keeper_bench_output:
        keeper_bench_write_result = {
            "result_write_total_requests": keeper_bench_output["write_results"]["total_requests"],
            "result_write_requests_per_second": keeper_bench_output["write_results"]["requests_per_second"],
            "result_write_bytes_per_second": keeper_bench_output["write_results"]["bytes_per_second"],
            "result_write_percentiles": keeper_bench_output["write_results"]["percentiles"],
        }
        result.update(keeper_bench_write_result)

    client = get_clickhouse_connect_client()

    try:
        client.insert(f"{TABLE_BENCH_INFO}", [list(result.values())], column_names=list(result.keys()))
    except Exception as e:
        logger.error(e)
        raise e

    # query = client.query_df(f"""select * from {TABLE_BENCH_INFO} where benchmark_id = '{str(benchmark_metric_result[0]['benchmark_id'])}' """)
    # print(query)

def start(args):
    # if args.config:
    #     try:
    #         with open(Path(__file__).resolve().parent / args.config) as f:
    #             config = yaml.safe_load(f)
    #         args = config_to_args(args_config)
    #     except Exception:
    #         logging.info("Unable to load config.yaml file")

    # Additional config and generate keeper bench yaml file
    keeper_bench_config = create_keeper_bench_config(args)
    print(f"keeper_bench_config: {keeper_bench_config}")
    generate_keeper_bench_yaml(keeper_bench_config)

    # 
    experiment_id = get_experiment_id(keeper_bench_config)
    benchmark_id = str(uuid.uuid4())

    logger.info(f"Starting experiment {experiment_id} and benchmark {benchmark_id}")

    _ = benchmark(keeper_bench_config['config_iterations'], keeper_bench_config['no_keeper_prometheus_metric'])
    (keeper_bench_output, benchmark_metric_result, is_successful, exception_message) = _

    for metric in benchmark_metric_result:
        metric.update({"experiment_id": experiment_id, "benchmark_id": benchmark_id, "host_info": keeper_bench_config["host_info"]})

    logger.info(f"Completed experiment {experiment_id} and benchmark {benchmark_id}")

    benchmark_ts = int(sorted([metric['prometheus_ts'] for metric in benchmark_metric_result])[0] / 1000.0)
    
    # for metric in benchmark_metric_result:
    #     for v in metric.values():
    #         if v is None:
    #             logger.error(str(metric))

    if is_successful:
        logger.info("Ok")
    else:
        logger.error("Not ok")

    # log to info    
    save_benchmark_info_result(experiment_id, benchmark_id, benchmark_ts, keeper_bench_config, keeper_bench_output, exception_message)
    
    # log to metric
    save_benchmark_metric_result(benchmark_metric_result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # read config file by default
    # parser.add_argument("--config", type=str, help="config", required=False, default='config.yaml')
    # experiment
    parser.add_argument("--num-repeat", type=int, help="num_repeat", required=False, default=10)
    parser.add_argument("--config-concurrency", type=int, help="config_concurrency", required=False, default=3)
    parser.add_argument("--config-iterations", type=int, help="config_iterations", required=False, default=10000)
    parser.add_argument("--workload-file", type=str, help="keeper-bench config file", required=False)
    # keeper
    parser.add_argument("--host-info", type=str, help="host_info", required=False)
    parser.add_argument("--keeper-type", type=str, help="keeper_type", required=False)
    parser.add_argument("--keeper-count", type=int, help="keeper_count", required=False)
    parser.add_argument("--keeper-cpu", type=int, help="keeper_cpu", required=False)
    parser.add_argument("--keeper-memory", type=str, help="keeper_memory", required=False)
    parser.add_argument("--keeper-jvm-memory", type=str, help="keeper_jvm_memory", required=False)
    parser.add_argument("--no-keeper-prometheus-metric", required=False, action="store_true") # true if flag is enabled

    parser.add_argument("--chkeeper_ports", nargs='+', help='chkeeper ports', required=False)
    parser.add_argument("--zookeeper_ports", nargs='+', help='zookeeper ports', required=False)

    args = parser.parse_args()

    start(args)

