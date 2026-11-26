# Mininet QoS TP3

This project compares baseline traffic with HTB QoS on the 10 Mbit/s link through virtual gateway g1.

Traffic: VoIP uses UDP port 5201 at 64 Kbit/s; video uses UDP port 5202 at 4 Mbit/s; bulk data uses TCP port 5203.

The qos_htb.sh script installs port filters and HTB scheduling classes on g1-eth1. The experiment runner records iperf3 metrics and HTB class counters.

## Reproduce the five-run comparison

sudo mn -c
sudo python3 scripts/run_experiment.py --condition baseline --runs 5 --duration 30
sudo mn -c
sudo python3 scripts/run_experiment.py --condition qos --qos-script ./scripts/qos_htb.sh --runs 5 --duration 30

## Low-load control

The realtime scenario runs VoIP and video without bulk TCP. It is one short control run.

sudo mn -c
sudo python3 scripts/run_experiment.py --condition baseline --scenario realtime --runs 1 --duration 10
sudo mn -c
sudo python3 scripts/run_experiment.py --condition qos --qos-script ./scripts/qos_htb.sh --scenario realtime --runs 1 --duration 10

## Results and graph

CSV and iperf3 JSON results are stored in results/. HTB counters are saved for QoS runs. Run sudo python3 scripts/plot_results.py to regenerate results/baseline_vs_qos.png.

