#!/usr/bin/env bash
# chkconfig: 345 95 20
# description: Run OBIEE temp space monitoring
#
# File:    /etc/init.d/monitor_nqs_temp.sh
# Description: OBIEE temp space monitoring
# Author: @rmoff / Rittman Mead Consulting, December 2015
# Absolutely no warranty, use at your own risk
#
# This script will capture information about the use of the OBIEE system component
# temp folders, giving us an idea of the ‘high watermark’, as well as general
# usage patterns.
#
#-------------------------------

case "$1" in
    start|startup)
	su - oracle --command /opt/obi-metrics-agent/obiee_monitor_temp/obiee_monitor_temp.sh
        ;;
    stop|shutdown)
	pkill -9 -f obiee_monitor_temp
    ;;
    *)
        echo "Usage: $(basename $0) start|stop"
        exit 1
esac

