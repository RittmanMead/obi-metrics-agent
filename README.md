# obi-metrics-agent.py							

	===================================================================
	Developed by @rmoff / Rittman Mead (http://www.rittmanmead.com)
	Absolutely no warranty, use at your own risk
	Please include this notice in any copy or reuse of the script you make
	===================================================================

## Introduction

**obi-metrics-agent** is a tool that extracts OBIEE's performance metrics from the [Dynamic Monitoring Service (**DMS**)](http://docs.oracle.com/cd/E23943_01/core.1111/e10108/dms.htm#CIHCFIFA) functionality. 

It works with OBIEE 11g and 12c.

## Overview

This application is written in Jython, to run under WLST. It will pull out all the OBIEE DMS metrics, and output them. Currently supported outputs are in Carbon/Graphite format, or native InfluxDB. Modifying the script to dump out CSV etc is trivial if you want to do so.

It's written to run under a scheduler such as crontab, and so will launch, collect metrics, and exit again.

## Setup

1. Provision your data store (eg InfluxDB). If using InfluxDB, create a database to hold the metrics 

		curl -G GET 'http://localhost:8086/query' --data-urlencode "q=CREATE DATABASE obi"

2. Run obi-metrics-agent.py to check everything works: 

		$FMW_HOME/oracle_common/common/bin/wlst.sh ~/obi-metrics-agent.py weblogic Admin123 t3://localhost:7001

3. Add to crontab : 

		0-59 * * * * /app/oracle/biee/oracle_common/common/bin/wlst.sh ~/obi-metrics-agent.py weblogic Admin123 t3://localhost:7001 2>/dev/null

## TODO

Better documentation ;)
Plus the stuff listed in the header of obi-metrics-agent.py itself
