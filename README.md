# obi-metrics-agent.py							

	@rmoff / March 2014

## LICENCE TO GO HERE


## Introduction
This is the same concept as Venkat’s original code. It differs as follows: 

* Single collector script (`obi-metrics-agent.py`), re-written in python
* In-built scheduler/timer
* Multiple output options: 
	* CSV
	* INSERT statements
	* Carbon, (for rendering in Graphite etc)
	* Unparsed XML
	* Unparsed raw opmn output
* Parse data as it is collected, or write to disk
* Parse data collected previously

As well as being core to performance testing, it could be used as a standard OBI monitoring tool (alongside EM etc).

---

## About the collector
### Which OBI metrics are collected?
All of the ones that OPMN supports. Currently, BI Server and BI Presentation Services, plus the opmn process metrics (CPU time of each OBI component)
### What about other metrics?

* OS metrics : collectl -> Carbon/Graphite  (or JMeter PerfMon)
* JVM metrics: Mission Control? 
### How are the metrics collected? 
Using the documented OPMN functionality to expose DMS metrics (`opmnctl metric op=query`)

### What are the installation requirements?

* Python (2.4.3, the version that ships on OEL 5.5, is fine)
* lxml
	* Could be optional, if only gathering raw data for processing later. Requires code change.

### Which platforms are supported?

* Tested thoroughly on OEL 5.5 and OL6.3
* Seems to work on Windows 2003

Python is cross-platform, so it ought to work on other platforms

### Known Issues (11.1.1.6)

There is a bug in the opmn process which causes corrupt XML sometimes. On the Exalytics box, this can sometimes be as much as 15% of samples. An SR was opened for this, SR 3-5811527931.

On corrupt samples, the datapoint is just dropped. 

The patch for this issue is 13055259. If patching the sample environment is not an option, then dropped data points will have to be accepted. 

### Limitations
Only single-node clusters are currently supported. Modification of the parsing code would probably be necessary to handle additional instances. 

### Installation on Unix

1. Put `obi-metrics-agent.py` into its own folder, for example, `/u01/app/obi-metrics-agent/`
	
	`git clone git@github.com:RittmanMead/scripts.git`
	
2. Check that python is available and at least v2.4.3:  

	python -V
	
3. Install lxml 

	sudo yum install python-devel python-setuptools libxml2-devel libxslt-devel
	sudo easy_install lxml
	
### Installation on Windows
1. Put `obi-metrics-agent.py` into its own folder, for example, `C:\ltpma\`
2. If not already, install Python: 
		* Windows x86: http://www.python.org/ftp/python/2.7.3/python-2.7.3.msi
		* Windows x86-64: http://www.python.org/ftp/python/2.7.3/python-2.7.3.amd64.msi
3. Install lxml (http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml). Make sure it's the right version (tested on 2.3) for the right python (2.7) and architecture (32/64)
		* Windows x86: lxml-2.3.4.win32-py2.7.exe
		* Windows x86-64: http://www.lfd.uci.edu/~gohlke/pythonlibs/eodybnto/lxml-2.3.6.win-amd64-py2.7.exe

### Optional : install collectl (not Windows)

`sudo yum install collectl`

---

## Using the collector
### Introduction

**obi-metrics-agent** collects OBI metrics data from DMS via opmn. It has three modes:  

1. Collect and parse metrics to output
2. Collect metrics to disk only
3. Parse existing metrics from disk

### Which mode to use?

1. Collect and parse metrics to output
	* Near-real-time rendering of OBI metrics in Graphite
	* Near-real-time load of data into Oracle (via CSV & external table)
2. Collect metrics to disk only
	* For analysis at a later date
	* If graphite/carbon is not available to send data to
	* If outbound network bandwidth is constrained (or could be, by OBIEE)
	* For lowest host system overhead
3. Parse existing metrics from disk
	* Parse previously collected data and output to Graphite or Oracle (via CSV & external table)

### Example usage
#### Collect and Parse - output to Carbon/Graphite

1. Initial Set up: 
	* Make sure there is a Carbon/Graphite server available (two easy options : Existing Amazon EC2 AMI, or Ubuntu VirtualBox image). Use `test_carbon.py` to test it if required
	* Configure the Carbon server’s /opt/graphite/conf/storage-schemas.conf for sample intervals you want to use eg 5 sec
2. Run **collectl** to send OS data to the Carbon server:   

		collectl -scdmnCDZ --export graphite,graphite_server:2003,p=.os.,s=cdmnCDZ
3. Run **obi-metrics-agent.py**

		obi-metrics-agent.py --output carbon --carbon-server graphite_server
4. View Graphite dashboards, by default at `http://<graphite_server>/dashboard/`

#### Collect and Parse - output to Oracle/OBIEE

1. Initial Set up:
	1. Edit `ddl.sql` CREATE DIRECTORY definition to point to the folder that holds the csv file (`data-directory` specified to obi-metrics-agent.py, see below)
	2. Run `ddl.sql` as SYSDBA. It will create a LTPMA user.
2. Collect OS stats with **collectl** to disk, or **JMeter PerfMon**
3. Run **obi-metrics-agent.py**

		obi-metrics-agent.py --output csv --data-directory ~/data
4. Viewing the output:
	1. Data can be queried directly through Oracle as OBI_METRICS_EXT
	2. Use Create Table As Select (CTAS) to copy data to permanent Oracle table
	3. Use OBIEE or alternative tool to render the data from the table
		
#### Collect metrics to disk (for processing at a later date)
1. Initial Set up: none
2. Collect OS stats with **collectl** to disk, or **JMeter PerfMon**
3. Run `obi-metrics-agent.py`

		obi-metrics-agent.py --output raw --data-directory ~/data

#### Parse existing metrics from disk, output to CSV file
1. Run `obi-metrics-agent.py`

		obi-metrics-agent.py --output csv --parse-only

#### Parse existing metrics from disk, output to Carbon/Graphite
1. Run `obi-metrics-agent.py`
	
		obi-metrics-agent.py --parse-only --output carbon --carbon-server localhost 
NB this may flood carbon and might need throttling; not clear how carbon handles an influx of data. *Maybe update obi-metrics-agent to send pickles for efficiency?*

#### Example usage on Windows

*Calling obi-metrics-agent on Windows is no different from calling it on Linux. Depending on how Python has been installed you may need to directly reference the Python executable*

	c:\Python27\python.exe c:\Users\Administrator\Documents\GitHub\ltpma\obi-metrics-agent\obi-metrics-agent.py --opmnbin c:\oracle\middleware\instances\instance1\bin\opmnctl.bat --output carbon --carbon-server rnm-ubu-01 --fmw-instance=WIN2k8



---
		
## Architecture
￼
![Architecture](architecture.png)

## Rendering the data
### Graphite
Graphite is an open-source graphing platform specifically for time-based metrics. It includes its own database (“whisper”) and database collector agent (“carbon”). 

Graphite is an optional target for obi-metrics-agent. The obi-metrics-agent can be deployed standalone.

Graphite as it is also supported by collectl, an OS monitoring tool favoured by the likes of Kevin Closson and Greg Rahn. 

Using graphite, any metrics held in its database can quickly be rendered into a graph. Because Graphite is all about time-based measurement, we can easily overlay OBI metrics with OS metrics in the same graphs. 

￼![Graphite screenshot](graphite01.png)

### Why not use OBIEE for drawing graphs? 
We can, if we want. The OBI metric data can be loaded in by external table from the CSV files, or using the generated INSERT statements. 

Using Graphite gives an alternative to a dependency on OBIEE because rendering the data on the system that we’re also testing complicates things. If we then set up a second OBIEE server just for rendering graphs then it opens up the question of what’s the best graphing tool for this particular job, and Graphite is a strong option here. 

### What are the system requirements for Graphite?

* Python 2.6
* Plus several other components.

I am currently running Graphite on an Ubuntu VM, and also have an Amazon Linux AMI with it available. It will work on OL6 but not natively on OL5 because of the early python version.

### Installing Graphite
* [Cribsheet 1](https://www.evernote.com/shard/s16/sh/7eb00bd7-2832-40ab-825f-1728cc568ca1/ca24ccc31636181150f210c1ff2c7e44)
* [Cribsheet 2](https://www.evernote.com/shard/s16/sh/4beff8ea-efd0-401d-b219-552db74246c9/118eec530d763a3a88afb68b58b13446)
* [Cribsheet 3](https://www.evernote.com/shard/s16/sh/32d67a7d-bb9d-4257-adf9-746ee0ec9174/b0ed92f849279a1ea7785eede4811c8e)

### Using Graphite
* [[ build metric graphs in composer ]]
* [[ set relative or absolute time ]]
* [[ Set time autorefresh ]]
* [[ build up dashboards from graphs ]]
* [[ export sqlite DB of predefined OBI/OS dashboards of standard metrics ]]

