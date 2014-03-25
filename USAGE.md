# Using obi-metrics-agent

**obi-metrics-agent** collects OBI metrics data from DMS via opmn. It has three modes:  

1. Collect and parse metrics to output
2. Collect metrics to disk only
3. Parse existing metrics from disk

## Which mode to use?

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

## Syntax

	Options:
	  -h, --help            show this help message and exit
	  -o OUTPUTFORMAT, --output=OUTPUTFORMAT
				The output format(s) of data, comma separated. More
				than one can be specified. Unparsed options: raw, xml
				Parsed options: csv , carbon, sql
	  -d DATA, --data-directory=DATA
				The directory to which data files are written. Not
				needed if sole output is carbon.
	  -p, --parse-only      If specified, then all raw and xml files specified in
				the data-directory will be processed, and output to
				the specified format(s) Selecting this option will
				disable collection of metrics.
	  --fmw-instance=FMW_INSTANCE
				Optional. The name of a particular FMW instance. This
				will be prefixed to metric names.
	  --carbon-server=CARBON_SERVER
				The host or IP address of the Carbon server. Required
				if output format 'carbon' specified.
	  --carbon-port=CARBON_PORT
				Alternative carbon port, if not 2003.
	  -i INTERVAL, --interval=INTERVAL
				The interval in seconds between metric samples.
	  --opmnbin=OPMN_BIN    The complete path to opmnctl. Watch out for spaces.

## Example usage

### Collect and Parse - output to Carbon/Graphite

1. Make sure there is a Carbon/Graphite server available 
3. Run **obi-metrics-agent.py**, specifying the `output carbon` and `carbon-server` parameters

		python $FMW_HOME/obi-metrics-agent/obi-metrics-agent.py --opmnbin $FMW_HOME/instances/instance1/bin/opmnctl --output carbon --carbon-server graphite_server
4. View Graphite dashboards, by default at `http://<graphite_server>/dashboard/`

### Collect and Parse - output to Oracle/OBIEE

1. Initial Set up:
	1. Prepare a script based on the DDL in the appendix below. Amend the CREATE DIRECTORY definition to point to the folder that holds the csv file (`data-directory` specified to obi-metrics-agent.py, see below)
	2. Execute the DDL as SYSDBA. It will create a user and external table definition.
3. Run **obi-metrics-agent.py** 
		python $FMW_HOME/obi-metrics-agent/obi-metrics-agent.py --opmnbin $FMW_HOME/instances/instance1/bin/opmnctl --output csv --data-directory ~/data
4. Viewing the output:
	1. Data can be queried directly through Oracle as DMS_METRICS_EXT
	2. Use Create Table As Select (CTAS) to copy data to permanent Oracle table
	3. Use OBIEE or alternative tool to render the data from the table
		
### Collect metrics to disk (for processing at a later date)
1. Initial Set up: none
3. Run `obi-metrics-agent.py`

		python $FMW_HOME/obi-metrics-agent/obi-metrics-agent.py --opmnbin $FMW_HOME/instances/instance1/bin/opmnctl --output raw --data-directory ~/data

### Parse existing metrics from disk, output to CSV file
1. Run `obi-metrics-agent.py`

		python $FMW_HOME/obi-metrics-agent/obi-metrics-agent.py --opmnbin $FMW_HOME/instances/instance1/bin/opmnctl --output csv --parse-only

### Parse existing metrics from disk, output to Carbon/Graphite
1. Run `obi-metrics-agent.py`
	
		python $FMW_HOME/obi-metrics-agent/obi-metrics-agent.py --opmnbin $FMW_HOME/instances/instance1/bin/opmnctl --parse-only --output carbon --carbon-server localhost 
*NB this may flood carbon and might need throttling; not clear how carbon handles an influx of data. *Maybe update obi-metrics-agent to send pickles for efficiency?*

## Appendix: DDL for accessing obi-metric-agent data in Oracle

	create user obi-metrics IDENTIFIED BY Password01;
	GRANT CONNECT, RESOURCE, CREATE ANY DIRECTORY TO obi-metrics;

	CONNECT obi-metrics/Password01

	CREATE TABLE DMS_METRICS (METRIC VARCHAR(250),VALUE INT,TIME_EPOCH INT);
	CREATE UNIQUE INDEX DMS_METRIC_IX ON DMS_METRICS (METRIC,TIME_EPOCH);

	CREATE OR REPLACE DIRECTORY DMS_DATA AS '/change/this/path/to/where/data/is/written/';

	DROP TABLE DMS_METRICS_EXT;
	CREATE TABLE DMS_METRICS_EXT (METRIC VARCHAR(250),VALUE INT,TIME_EPOCH INT)
	ORGANIZATION EXTERNAL
	(TYPE ORACLE_LOADER
	     DEFAULT DIRECTORY DMS_DATA
	     ACCESS PARAMETERS
	       (records delimited BY newline
		fields
		    terminated BY ','
		    optionally enclosed BY '"'
		    missing field VALUES are NULL
	      )
	     LOCATION ('metrics.csv')
	  );

	exit


