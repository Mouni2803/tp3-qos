#!/usr/bin/env python3
"""Run concurrent VoIP, video, and bulk tests on the G1 Mininet topology."""

import argparse
import csv
import json
import os
import shlex
import subprocess
import sys
import time

from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import OVSBridge
from topo_g1 import G1Topo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition", choices=("baseline", "qos"), required=True)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--duration", type=int, default=10)
    parser.add_argument("--qos-script", default=None)
    args = parser.parse_args()

    if args.condition == "qos" and not args.qos_script:
        parser.error("QoS condition needs --qos-script")
    return args


def configure_routes(net):
    g1 = net.get("g1")
    g1.cmd("ip addr flush dev g1-eth0")
    g1.cmd("ip addr flush dev g1-eth1")
    g1.cmd("ip addr add 10.0.4.1/24 dev g1-eth0")
    g1.cmd("ip addr add 10.0.5.1/24 dev g1-eth1")
    g1.cmd("sysctl -w net.ipv4.ip_forward=1")

    for name in ("h1", "h2", "h3"):
        net.get(name).cmd("ip route replace default via 10.0.4.1")
    for name in ("srv1", "srv2", "srv3"):
        net.get(name).cmd("ip route replace default via 10.0.5.1")


def read_iperf(path, flow):
    with open(path, encoding="utf-8") as file:
        data = json.load(file)

    end = data["end"]
    if flow == "bulk_tcp":
        received = end["sum_received"]["bits_per_second"] / 1_000_000
        retransmits = end.get("sum_sent", {}).get("retransmits", "")
        return received, "", "", retransmits

    summary = end.get("sum_received", end.get("sum", {}))
    return (
        summary.get("bits_per_second", 0) / 1_000_000,
        summary.get("jitter_ms", ""),
        summary.get("lost_percent", ""),
        "",
    )


def main():
    args = parse_args()
    if args.runs < 1 or args.duration < 1:
        sys.exit("--runs and --duration must be positive")

    os.makedirs(RESULTS, exist_ok=True)
    label = "%s_%druns_%ds" % (args.condition, args.runs, args.duration)
    csv_path = os.path.join(RESULTS, label + ".csv")
    write_header = not os.path.exists(csv_path)

    net = Mininet(
        topo=G1Topo(bottleneck=True),
        switch=OVSBridge,
        link=TCLink,
        controller=None,
    )

    try:
        net.start()
        configure_routes(net)
        g1 = net.get("g1")

        if args.qos_script:
            script = os.path.abspath(args.qos_script)
            output = g1.cmd("bash " + shlex.quote(script))
            print(output.strip())
            classes = g1.cmd("tc class show dev g1-eth1")
            required = (
                "class htb 1:1",
                "class htb 1:10",
                "class htb 1:20",
                "class htb 1:30",
            )
            if not all(item in classes for item in required):
                raise RuntimeError("HTB classes were not installed on g1-eth1")

        for host, port in (("srv1", 5201), ("srv2", 5202), ("srv3", 5203)):
            net.get(host).cmd("iperf3 -s -p %d -D" % port)
        time.sleep(1)

        with open(csv_path, "a", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            if write_header:
                writer.writerow((
                    "condition", "run", "flow", "throughput_mbps",
                    "jitter_ms", "loss_pct", "tcp_retransmits"
                ))

            for run in range(1, args.runs + 1):
                stem = "%s_run_%02d" % (label, run)
                specs = (
                    (
                        "voip", "h1",
                        ["iperf3", "-J", "-c", "10.0.5.21", "-p", "5201",
                         "-u", "-b", "64K", "-l", "160", "-t",
                         str(args.duration)]
                    ),
                    (
                        "video", "h2",
                        ["iperf3", "-J", "-c", "10.0.5.22", "-p", "5202",
                         "-u", "-b", "4M", "-t", str(args.duration)]
                    ),
                    (
                        "bulk_tcp", "h3",
                        ["iperf3", "-J", "-c", "10.0.5.23", "-p", "5203",
                         "-t", str(args.duration)]
                    ),
                )

                jobs = []
                paths = {}
                for flow, host, command in specs:
                    path = os.path.join(RESULTS, stem + "_" + flow + ".json")
                    output_file = open(path, "w", encoding="utf-8")
                    process = net.get(host).popen(
                        command,
                        stdout=output_file,
                        stderr=subprocess.STDOUT,
                    )
                    jobs.append((flow, process, output_file))
                    paths[flow] = path

                for flow, process, output_file in jobs:
                    code = process.wait()
                    output_file.close()
                    if code != 0:
                        raise RuntimeError(
                            "iperf3 failed for %s; see %s" % (flow, paths[flow])
                        )

                for flow, _, _ in specs:
                    throughput, jitter, loss, retransmits = read_iperf(
                        paths[flow], flow
                    )
                    writer.writerow((
                        args.condition, run, flow, round(throughput, 4),
                        jitter, loss, retransmits
                    ))
                    print(
                        "run %d %s: %.3f Mbit/s" % (run, flow, throughput)
                    )

                if args.condition == "qos":
                    stats_path = os.path.join(RESULTS, stem + "_classes.txt")
                    with open(stats_path, "w", encoding="utf-8") as stats_file:
                        stats_file.write(
                            g1.cmd("tc -s class show dev g1-eth1")
                        )
                    print("Class counters saved to " + stats_path)

    finally:
        net.stop()


if __name__ == "__main__":
    setLogLevel("error")
    main()

