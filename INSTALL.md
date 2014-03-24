# Installing obi-metric-agent 

There are three parts to the obi-metrics-agent installation. Only one of these is mandatory - the installation of obi-metrics-agent itself. 

1. `obi-metrics-agent` - python script to extract DMS metrics from OBIEE
2. `collectl` - OS metrics viewer. Can send data for graphing in Graphite
3. Graphite - store and graph data, including that extracted from `obi-metrics-agent` and `collectl`
4. You have the EPEL yum repository setup (for packages such as git, etc): 
	* OL 5/Cent OS 5/RHEL 5  (including SampleApp v309R2):

			sudo rpm -Uvh http://download.fedoraproject.org/pub/epel/5/i386/epel-release-5-4.noarch.rpm
	* OL 6/Cent OS 6/RHEL 6:

			sudo rpm -Uvh http://dl.fedoraproject.org/pub/epel/6/`uname -p`/epel-release-6-8.noarch.rpm

## Installation from script

[[TODO / see blog post]] 

## 1. Installing obi-metrics-agent

**obi-metrics-agent** just requires python (minimum 2.4), and the lxml library. 

### Installation on Linux

####  Install XML lib

**obi-metrics-agent** needs the lxml library, which can be installed as follows:

	sudo yum install -y libxslt-devel python-setuptools
	sudo easy_install lxml

#### Install obi-metrics-agent script

**obi-metrics-agent** is downloaded by cloning the git repository. This will bring in the python script itself, documentation and the installation scripts for graphite (see below)

On Linux, do the following, setting the value for `FMW_HOME` accordingly: 

	sudo yum install -y git
	export FMW_HOME=/home/oracle/obiee # Change this value for your installation
	cd $FMW_HOME
	git clone https://github.com/RittmanMead/obi-metrics-agent.git

This will install git (if not present), and create a folder called **obi-metrics-agent** in the installation folder of OBIEE (FMW Home). You can put obi-metrics-agent wherever you want, this locating is just a suggestion. 

### Installation on Windows

1. Using git, clone the github repository [https://github.com/RittmanMead/obi-metrics-agent.git](https://github.com/RittmanMead/obi-metrics-agent.git) or [download the python script directly](https://raw.github.com/RittmanMead/obi-metrics-agent/master/obi-metrics-agent.py)
2. If not already, install Python:
	* Windows x86: http://www.python.org/ftp/python/2.7.3/python-2.7.3.msi
	* Windows x86-64: http://www.python.org/ftp/python/2.7.3/python-2.7.3.amd64.msi
3. Install lxml (http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml). Make sure it's the right version (tested on 2.3) for the right python (2.7) and architecture (32/64)
	* Windows x86: lxml-2.3.4.win32-py2.7.exe
	* Windows x86-64: http://www.lfd.uci.edu/~gohlke/pythonlibs/eodybnto/lxml-2.3.6.win-amd64-py2.7.exe

### Testing obi-metrics-agent

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

## 2. Installing collectl [optional]

`collectl` is an OS monitoring / metrics collection tool. To install on OL5/6 simply run: 

	sudo yum install -y collectl

Once installed, you can enter `collectl` to run it interactively. Alternatively you can set `collectl` to start automatically at boot time, where it will write its data to /var/log/collectl from where you can analyse it at your leisure

	sudo chkconfig --level 35 collectl on

To start collectl as a daemon manually: 

	sudo service collectl start

To configure it as a daemon (background process) to continually send OS data to graphite/carbon, amend amend the collectl configuration file:

	sudo sed -i.bak -e 's/DaemonCommands/#DaemonCommands/g' /etc/collectl.conf
	sudo sed -i -e '/DaemonCommands/a DaemonCommands = -f \/var\/log\/collectl -P -m -scdmnCDZ --export graphite,localhost:2003,p=.os.,s=cdmnCDZ' /etc/collectl.conf

Optionally, set to collect every five seconds: 

	sudo sed -i -e '/#Interval =     10/a Interval = 5' /etc/collectl.conf

Extensive documentation about collectl, including additional configuration information and example usage, can be found on [the collectl homepage](http://collectl.sourceforge.net/)


## 3. Installing Graphite [optional]

Graphite is an open-source graphing tool, incorporating its own database. You don’t have to install Graphite to use obi-metrics-agent but it is a very good way to easily visualise the data that you collect. If you want to install it there are fully automated installation scripts, along with installation walk-throughs, provided. Details vary slightly depending on the version of your OS. Do note that Graphite is somewhat notorious for installation problems, so whilst these instructions have been tested, you may hit quirks on your own server that may need a bit of Google-Fu to resolve.

Assuming you have cloned the obi-metrics-agent GitHub repository as shown above, then to run the graphite installation script run the following:

	export FMW_HOME=/home/oracle/obiee # Change this value for your installation
	cd $FMW_HOME/obi-metrics-agent
	./install-graphite-ol5.sh

If you’re on OL6 then simply run `install-graphite-ol6.sh` instead.

The installation script takes about 5 minutes to run.

If you want to follow step-by-step instructions detailing each step, they are provided:

* [Oracle Linux 5](INSTALL_GRAPHITE_OL5.md) (including Cent OS 5 and RHEL 5)
* [Oracle Linux 6](INSTALL_GRAPHITE_OL5.md) (including Cent OS 6 and RHEL 6)

If you’re on a different *nix platform then feel free to adapt the install scripts and submit a pull request. Graphite works flawlessly on Debian-based distributions, and there is no reason why you should run it local to the OBIEE server on which obi-metrics-agent is running.

