# Installing obi-metric-agent

*This assumes you are working in the same virtualenv as described in the graphite installation instructions ([OL5](INSTALL-GRAPHITE-OL5.md)/[OL6](INSTALL-GRAPHITE-OL6.md). If you are using a different python environment, you'll need to modify the `source` path.

## Install XML lib

	sudo yum install -y libxslt-devel
	source /home/oracle/graphite/bin/activate
	pip install lxml

## Install obi-metrics-agent script

	export FMW_HOME=/home/oracle/obiee # Change this value for your installation
	cd $FMW_HOME
	git clone https://github.com/RittmanMead/obi-metrics-agent.git
	
## Testing obi-metrics-agent

Assuming the OBIEE stack and carbon agent (part of Graphite) is running, the following should succeed: 

	export FMW_HOME=/home/oracle/obiee # Change this value for your installation
	source /home/oracle/graphite/bin/activate
	python $FMW_HOME/obi-metrics-agent/obi-metrics-agent.py --opmnbin $FMW_HOME/instances/instance1/bin/opmnctl --output=carbon --carbon-server=localhost

Expected output: 

	--Gather metrics--
		Time of sample: Wed, 19 Mar 2014 17:11:05 +0000 (1395249065)

		Get metrics for coreapplication_obips1
			 Processed :    469 data values @ Wed, 19 Mar 2014 17:11:05 +0000       Oracle BI Presentation Server
				Sent data to Carbon at localhost
		Get metrics for coreapplication_obis1
			 Processed :    229 data values @ Wed, 19 Mar 2014 17:11:05 +0000       Oracle BI Server
				Sent data to Carbon at localhost
		Get metrics for opmn
			 Processed :    91 data values @ Wed, 19 Mar 2014 17:11:05 +0000        opmn
				Sent data to Carbon at localhost

		Processed: 3    Valid: 3 (100.00%)      Invalid: 0 (0.00%)
		-- Sleeping for 5 seconds (until 1395249065)--

	--Gather metrics--
		Time of sample: Wed, 19 Mar 2014 17:11:10 +0000 (1395249070)

		Get metrics for coreapplication_obips1
			 Processed :    469 data values @ Wed, 19 Mar 2014 17:11:10 +0000       Oracle BI Presentation Server
	[...]
	[...]
	[...]
	[...]
	[...]
