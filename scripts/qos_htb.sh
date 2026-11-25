#!/bin/sh
DEV=g1-eth1

tc qdisc del dev "$DEV" root 2>/dev/null || true
tc qdisc add dev "$DEV" root handle 1: htb default 30
tc class add dev "$DEV" parent 1: classid 1:1 htb rate 10mbit ceil 10mbit

tc class add dev "$DEV" parent 1:1 classid 1:10 htb rate 1mbit ceil 10mbit prio 0
tc class add dev "$DEV" parent 1:1 classid 1:20 htb rate 3mbit ceil 10mbit prio 1
tc class add dev "$DEV" parent 1:1 classid 1:30 htb rate 1mbit ceil 10mbit prio 2

tc filter add dev "$DEV" protocol ip parent 1: prio 1 u32 match ip dport 5201 0xffff flowid 1:10
tc filter add dev "$DEV" protocol ip parent 1: prio 1 u32 match ip dport 5202 0xffff flowid 1:20
tc filter add dev "$DEV" protocol ip parent 1: prio 1 u32 match ip dport 5203 0xffff flowid 1:30

echo "HTB classes applied on $DEV"
