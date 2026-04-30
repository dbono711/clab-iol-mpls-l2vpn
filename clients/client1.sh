#!/bin/bash

# create VLAN interface for RED service
ip link add name eth1.10 link eth1 type vlan id 10
ip link set dev eth1.10 up

## create IPv4 address for RED service
ip addr add 172.16.1.1/30 dev eth1.10
