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
# Update FMW_BASE, and OUT_BASE if you want to (it’s where it’ll write the files, /tmp by default)
#
# The assumption is that under FMW_BASE you may have multiple FMW_HOMEs, eg:
#   FMW_BASE=/oracle
# Which would then monitor the BI Server temp for three FMW_HOMEs:
#   /oracle/FMW_DEV/instances/instances1/[...]
#   /oracle/FMW_TEST/instances/instances1/[...]
#   /oracle/FMW_UAT/instances/instances1/[...]
#
FMW_BASE=/app/oracle
#
# This is the base path used for constructing the output filenames
OUT_BASE=/u01/data/obi-temp/obiee
#
# How frequently to poll.
INTERVAL=10
#
# How much data to log. 
# (1=space used, 2=plus filesystems, 3=plus list of contents)
LEVEL=1
#------------------------------------------------------------------------------------------------


function monitor_obis_temp() {
  FMW_HOME=$FMW_BASE/$1
  OUT_BASE=$OUT_BASE.$1
  echo "Writing diagnostics for BI Server temp in $FMW_HOME to $OUT_BASE every $INTERVAL seconds, level $LEVEL (1=space used, 2=plus filesystems, 3=plus list of contents)"

  while [ 1 -eq 1 ]; do
    if [[ $LEVEL -ge 1 ]]; then
        echo -e $1'\t'$(date +%s)'\t'$(date +%Y-%m-%dT%H:%M:%S)'\tOracleBIServerComponent\t'$(du -s $FMW_HOME/instances/instance1/tmp/OracleBIServerComponent/coreapplication_obis1/obis_temp|awk '{print $1}') >> $OUT_BASE.du.tsv
        echo -e $1'\t'$(date +%s)'\t'$(date +%Y-%m-%dT%H:%M:%S)'\tOracleBIJavaHostComponent\t'$(du -s $FMW_HOME/instances/instance1/tmp/OracleBIJavaHostComponent/coreapplication_obijh1/|awk '{print $1}') >> $OUT_BASE.du.tsv
        echo -e $1'\t'$(date +%s)'\t'$(date +%Y-%m-%dT%H:%M:%S)'\tOracleBIPresentationServicesComponent\t'$(du -s $FMW_HOME/instances/instance1/tmp/OracleBIPresentationServicesComponent/coreapplication_obips1/|awk '{print $1}') >> $OUT_BASE.du.tsv
    fi
    if [[ $LEVEL -ge 2 ]]; then
        echo -e $1'\t'$(date +%s)'\t'$(date +%Y-%m-%dT%H:%M:%S)'\t'$(df $FMW_HOME/instances/instance1/tmp/OracleBIServerComponent/coreapplication_obis1/obis_temp|tail -n1) >> $OUT_BASE.df.tsv
    fi
    if [[ $LEVEL -ge 3 ]]; then
        echo -e '---\n'$1'\t'$(date +%s)'\t'$(date +%Y-%m-%dT%H:%M:%S)'\n'$(ls -l $FMW_HOME/instances/instance1/tmp/OracleBIServerComponent/coreapplication_obis1/obis_temp) >> $OUT_BASE.ls.log
    fi
    sleep $INTERVAL
  done
}


SCRIPTNAME=$0
PIDCOUNT=$(ps -ef|grep $SCRIPTNAME|grep bash|wc -l)
# wc -l returns 2 for a single running proc, because the other proc is our own grep (thanks, Andy P!)
# >2 means there really are multiple procs running.
if [[ $PIDCOUNT -gt 2 ]]; then
  echo 'monitor_nqs_temp process is already running.  Exiting.'
  exit 2
fi

for dir in $(ls $FMW_BASE)
do
  if [ -d "$FMW_BASE/$dir/instances" ]; then
      monitor_obis_temp $dir &
  else
    echo 'Ignoring '$dir' as it doesn''t look like a FMW_HOME'
  fi
done
