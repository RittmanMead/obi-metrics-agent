# Installing obi-metric-agent 

## Installation on Linux

*This assumes you are working in the same virtualenv as described in the graphite installation instructions ([OL5](INSTALL-GRAPHITE-OL5.md)/[OL6](INSTALL-GRAPHITE-OL6.md). If you are using a different python environment, you'll need to modify the `source` path.

### Install XML lib

	sudo yum install -y libxslt-devel
	source /home/oracle/graphite/bin/activate
	pip install lxml

### Install obi-metrics-agent script

	export FMW_HOME=/home/oracle/obiee # Change this value for your installation
	cd $FMW_HOME
	git clone https://github.com/RittmanMead/obi-metrics-agent.git
	
## Installation on Windows

1. Using git, clone the github repository [https://github.com/RittmanMead/obi-metrics-agent.git](https://github.com/RittmanMead/obi-metrics-agent.git) or [download the python script directly](https://raw.github.com/RittmanMead/obi-metrics-agent/master/obi-metrics-agent.py)
2. If not already, install Python:
	* Windows x86: http://www.python.org/ftp/python/2.7.3/python-2.7.3.msi
	* Windows x86-64: http://www.python.org/ftp/python/2.7.3/python-2.7.3.amd64.msi
3. Install lxml (http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml). Make sure it's the right version (tested on 2.3) for the right python (2.7) and architecture (32/64)
	* Windows x86: lxml-2.3.4.win32-py2.7.exe
	* Windows x86-64: http://www.lfd.uci.edu/~gohlke/pythonlibs/eodybnto/lxml-2.3.6.win-amd64-py2.7.exe

## Testing obi-metrics-agent

Assuming the OBIEE stack is running, the following should succeed: 

	# Omit the "source" command if you're not using virtualenv
	source /home/oracle/graphite/bin/activate
	export FMW_HOME=/home/oracle/obiee # Change this value for your installation
	python $FMW_HOME/obi-metrics-agent/obi-metrics-agent.py --opmnbin $FMW_HOME/instances/instance1/bin/opmnctl 

Expected output: 

	[...]
	--Gather metrics--
		Time of sample: Wed, 19 Mar 2014 22:27:42 +0000 (1395268062)

		Get metrics for coreapplication_obips1
			 Processed :    469 data values @ Wed, 19 Mar 2014 22:27:42 +0000       Oracle BI Presentation Server
				Appended CSV data to ./data/metrics.csv
		Get metrics for coreapplication_obis1
			 Processed :    229 data values @ Wed, 19 Mar 2014 22:27:42 +0000       Oracle BI Server
				Appended CSV data to ./data/metrics.csv
		Get metrics for opmn
			 Processed :    91 data values @ Wed, 19 Mar 2014 22:27:42 +0000        opmn
				Appended CSV data to ./data/metrics.csv

		Processed: 3    Valid: 3 (100.00%)      Invalid: 0 (0.00%)
		-- Sleeping for 5 seconds (until 1395268062)--
	[...]

## Installing Graphite

Graphite is an open-source graphing tool, incorporating its own database. You don't have to install Graphite to use obi-metrics-agent but it is a very good way to easily visualise the data that you collect. If you want to install it there are fully automated installation scripts, along with installation walk-throughs, provided. Details vary slightly depending on the version of your OS:

* [Oracle Linux 5](INSTALL_GRAPHITE_OL5.md) (including Cent OS 5 and RHEL 5)
* [Oracle Linux 6](INSTALL_GRAPHITE_OL5.md) (including Cent OS 6 and RHEL 6)
