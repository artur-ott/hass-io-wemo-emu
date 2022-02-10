#!/bin/bash

start() {
  exec 2>/dev/null
  ip link delete wemo-vlan
  ip link add wemo-vlan link eth0 type macvlan mode bridge
  ip addr add 192.168.1.222/32 dev wemo-vlan
  ip link set wemo-vlan up
  ifconfig wemo-vlan hw ether A2:98:39:2D:7F:F7
  ip route add 192.168.1.2/32 dev wemo-vlan
  docker network rm hue_hub
  docker network create -d macvlan --subnet=192.168.1.0/24 --gateway 192.168.1.1 --aux-address 'host=192.168.1.222' -o parent=eth0 -o macvlan_mode=bridge hue_hub
  cd /var/wemo_emu
  docker-compose down
  docker-compose up -d
}

stop() {
  cd /var/wemo_emu
  docker-compose down
}

case $1 in
  start|stop) "$1" ;;
esac
