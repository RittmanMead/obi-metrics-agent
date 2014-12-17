#!/usr/bin/python
#
# obi-metrics-agent.py
#
# @rmoff / March 2014
# Inspired by Venkat's original java implementation
#
# ===================================================================
# Developed by @rmoff / Rittman Mead (http://www.rittmanmead.com)
# Absolutely no warranty, use at your own risk
# Please include this notice in any copy or reuse of the script you make
# ===================================================================#
#
# -------------------------------------------------
# Purpose: 
# This script gathers OBI metrics and sends them to Carbon for graphing in Graphite, or output to file (unprocessed XML including header, or CSV)
#
# CSV file could be used as source for external table to get the data into Oracle easily
#
# ---
# Known problems: 
#   If OBI Scheduler isn't running, parsing OPMN process metrics will fail (**Error parsing metric data: no such child: noun)
#   invalid_files.txt doesn't get written to 
#
# XML file structures currently handled:
#  OPMN OBIS, OBIPS metrics
#  OPMN process metrics
#
# Usage:
#  obi-metrics-agent.py
#
# Pre-requisites : lxml
#   sudo yum install libxml2-devel 
#   sudo easy_install lxml
#
# To Do:
#  Refactor into proper functions/procs
#  Error handling
#  Proper configuration file and checking
#
#
import time
import os
import sys
import subprocess
import socket
import datetime
import platform
from glob import glob
from optparse import OptionParser
from lxml import objectify

def parse_xml(xml):
	metrics_msg = []
	metrics_list = []
	global valid_xml
	global invalid_xml
	try:
		root = objectify.fromstring(xml)

		# Parse XML
		host = root.attrib['host']
		if FMW_INSTANCE is not None:
			host = '%s.%s' % (host,FMW_INSTANCE.upper())
		header_process_name = root.attrib['name']
		ts_epoch_msec = root.attrib['timestamp']
		ts_epoch = int(ts_epoch_msec)/ 1000
		
		#Check if platform is windows. If it is, adjust ts_epoch as windows uses Jan 01, 1601 as epoch
		if (platform.system() == 'Windows') :
			epoch_delta = (datetime.datetime(1970,1,1) - datetime.datetime(1601,1,1)).total_seconds()
			ts_epoch = ts_epoch - epoch_delta
		
		ts= time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime(ts_epoch))
		

		if (header_process_name == 'Oracle BI Server' or header_process_name == 'Oracle BI Presentation Server') :
			# Assumption is that this is a BIS or BIPS pdml file
			# BI Metrics
			n= root.statistics.noun[0]
			for n1 in root.statistics.noun[0].noun:
				group = (n1.attrib['type'] + "." + n1.attrib['name'])
				for metric in n1.metric:
					metric_name = metric.attrib['name'].replace('.value','').replace('.','').replace('/','-').replace('(','').replace(')','')
					metric_value= metric.value
					metric_full_name = (host + ".OBI." + group + "." + metric_name).replace(' ','_').replace('(','').replace(')','')
					metric_out = metric_full_name + " " + str(metric_value) + " " + str(ts_epoch)
					metrics_list.append((metric_full_name, str(metric_value) , str(ts_epoch)))
					metrics_msg.append(metric_out)

			# DMS Process metrics
			n= root.statistics.noun[1]
			group = (n.attrib['type'] + "." + n.attrib['name'] + "." + header_process_name)
			for metric in root.statistics.noun[1].metric:
				metric_type = metric.value.attrib['type']
				if metric_type == 'string':
					pass
				else:
					metric_name = metric.attrib['name'].replace('.value','')
					metric_value= metric.value
					metric_full_name = (host + ".DMS." + group + "." + metric_name).replace(' ','_')
					metric_out = metric_full_name + " " + str(metric_value) + " " + str(ts_epoch)
					metrics_list.append((metric_full_name, str(metric_value) , str(ts_epoch)))
					metrics_msg.append(metric_out)
		elif header_process_name == 'opmn' :
			# OPMN Metrics
			instance = root.statistics.noun[0].noun[1].noun[1]
			for component in instance.noun:
				process_type = component.noun[0]
				process_set = process_type.noun[0]
				process_name = process_set.attrib['name']
				for metric in process_set.metric:
					metric_type = metric.value.attrib['type']
					if metric_type == 'string':
						pass
					else:
						metric_full_name = host + '.Process.' + metric.attrib['name'].replace('.value','').replace('.count','') + '.'+ process_name
						metric_value = metric.value
						metric_out = metric_full_name + " " + str(metric_value) + " " + str(ts_epoch)
						metrics_list.append((metric_full_name, str(metric_value) , str(ts_epoch)))
						metrics_msg.append(metric_out)
				for metric in process_set.noun[0].metric:
					metric_type = metric.value.attrib['type']
					if metric_type == 'string':
						pass
					else:
						metric_full_name = host + '.Process.' + metric.attrib['name'].replace('.value','').replace('.count','') + '.'+ process_name
						metric_value = metric.value
						metric_out = metric_full_name + " " + str(metric_value) + " " + str(ts_epoch)
						metrics_list.append((metric_full_name, str(metric_value) , str(ts_epoch)))
						metrics_msg.append(metric_out)
		else :
			print ' *** PDML not recognised *** '
			print ' Name in header : ' % (header_process_name)
			return 3


	except Exception, err:
		invalid_xml += 1
		sys.stderr.write('\t**Error parsing metric data: %s\n' % str(err))
		try:
			file = open('%s/invalid_files.txt' % (DATA),'a')
			file.write(filename + '\n')
			file.close()
		except:
			pass
		return 2

	valid_xml += 1
	# more output conditions here - reformat into CSV (easy) and INSERT statements (not so easy)
	print '\t\t Processed : \t%d data values @ %s \t%s' % (len(metrics_msg),ts,header_process_name)
	if (len(metrics_msg) > 0) :
		# Do something with the data
		if do_output_csv:
			csvline = '\n'.join(metrics_msg).replace(' ',',') + '\n'
			csvfile = open('%s/metrics.csv' % (DATA),'a')
			csvfile.write(csvline)
			print '\t\t\tAppended CSV data to %s' % (csvfile.name)
			csvfile.close()
		if do_output_carbon:
			try:
				# Send data to carbon
				carbon_message = '\n'.join(metrics_msg) + '\n'
				sock = socket.socket()
				sock.settimeout(5)
				sock.connect((CARBON_SERVER, CARBON_PORT))
				#print 'sending message:\n%s' % message
				#print 'Sending message to carbon server %s' % (CARBON_SERVER)
				sock.sendall(carbon_message)
				sock.close()
				print '\t\t\tSent data to Carbon at %s' % (CARBON_SERVER)
			except Exception, err:
				sys.stderr.write('\t**Error sending data to Carbon: %s\n' % str(err))
		if do_output_sql:
			try:
				# Write an INSERT statement
				sql =''
				for line in metrics_list:
					metr,value,ts = line
					sql += "INSERT INTO OBI_METRICS (METRIC,VALUE,TIME_EPOCH) VALUES('%s',%d,%d);\n" % (metr,int(value),int(ts))
				sqlfile = open('%s/inserts.sql' % (DATA),'a')
				sqlfile.write(sql)
				print '\t\t\tWritten SQL INSERT statement to %s' % (sqlfile.name)
				sqlfile.close()
			except Exception, err:
				sys.stderr.write('\t**Error writing SQL: %s\n' % str(err))
	else:
		print '(No data - no action)'
	return 0

def get_metrics(opmn_cmd,outfile):
	try:
		component='COMPONENT_NAME=%s' % (opmn_cmd)
		outputfile=open(outfile,'w')
		p = subprocess.Popen([OPMN_BIN,'metric','op=query',component,'format=xml'],stdout=outputfile)
		rc = p.wait()
		#print '%s\t%d' % (opmn_cmd,outputfile.tell())
		outputfile.close()
		outputfile=open(outfile,'r')
		out = outputfile.read()
		outputfile.close()
		return out
	except Exception, err:
		sys.stderr.write('\n\t**get_metric : Error calling OPMN: %s\n' % str(err))
		sys.exit()

def collect_metrics():
	try:
		p = subprocess.Popen([OPMN_BIN,'status'],stdout=subprocess.PIPE)
		p.wait()
		opmnout = p.stdout.read()
		p.stdout.close()
		if opmnout.find('opmn is not running')>-1:
			sys.stderr.write('\nExiting : \n\t**OPMN is not running, so metrics cannot be collected\n')
			sys.exit()
	except Exception, err:
		sys.stderr.write('\n\tcollect_metrics: Error calling OPMN \n%s\n' % str(err))
		sys.exit()

	while True:
		thisTime = time.time()
		nextTime = thisTime + interval
		print '\n--Gather metrics--'
		print "\tTime of sample: %s (%d)\n " % (time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime(thisTime)),thisTime)
		for cmd in opmn_cmds:
			component=cmd

			# Call the opmn command
			if do_output_raw:
				filename='%s/%s_%d.raw' % (DATA,component,thisTime)
			else:
# Need to make this cross-platform
#				filename='/dev/shm/obimetric.tmp'
				filename='%s/data.raw' % (DATA)
			print '\tGet metrics for %s' % (component)
			raw = get_metrics(cmd,filename)
			if len(raw) < 100:
				print '\n\t ** Output returned from opmn is unexpectedly short, is there a problem? Output follows: \n\t\t%s' % (raw)
			if do_output_raw:
				print '\t\t\tWritten raw output to %s' % (filename)

			# Strip the first 101 bytes from the response - this is the HTTP header
			xml=raw[101:]
			if do_output_xml:
				# dump XML to file
				filename='%s/%s_%d.xml' % (DATA,component,thisTime)
				xml_file=open(filename,'w')
				xml_file.write(xml)
				xml_file.close()
				print '\t\t\tWritten XML output to %s' % (filename)

			# Process the XML returned from OPMN
			if do_output_sql or do_output_carbon or do_output_csv:
				parse_xml(xml)
				total_xml=valid_xml+ invalid_xml
				if total_xml == 0:
					perc_invalid_xml=0
				else:
					perc_invalid_xml = (invalid_xml / total_xml) *100
					perc_valid_xml = (valid_xml / total_xml) *100

		if do_output_sql or do_output_carbon or do_output_csv:
			print '\n\tProcessed: %d\tValid: %d (%0.2f%%)\tInvalid: %d (%0.2f%%)' % (total_xml,valid_xml,perc_valid_xml,invalid_xml,perc_invalid_xml)
		print '\t-- Sleeping for %d seconds (until %d)--' % (interval,nextTime)
		while nextTime > time.time():
			time.sleep((nextTime-time.time()))

def parse_files():
	# How to express raw OR xml in a single regex? would need to cater for raw files and stripping header, but rest of code could be combined
	base_path = '%s%s' % (DATA,os.sep)

	raw_files_path = base_path + '*.raw'
	raw_files = glob(raw_files_path)
	if len(raw_files) > 0 :
		print 'Processing raw files:'
		for filename in raw_files:
			print filename
			file = open(filename,'r')
			xml = file.read()[101:]
			file.close()
			if parse_xml(xml) == 0:
				os.rename(filename,filename +'.processed')
				print '\tSuccessfully processed %s and renamed it to %s' % (filename,filename +'.processed')
			else:
				os.rename(filename,filename +'.err')
				print '\tError processing %s. File renamed to %s' % (filename,filename +'.err')
	else:
		print '\n** No raw files found to process in %s\n' % (raw_files_path)

	xml_files_path = base_path + '*.xml'
	xml_files = glob(xml_files_path)
	if len(xml_files) > 0 :
		print 'Processing xml files:'
		for filename in xml_files:
			print filename
			file = open(filename,'r')
			xml = file.read()
			file.close()
			if parse_xml(xml) == 0:
				os.rename(filename,filename +'.processed')
				print '\tSuccessfully processed %s and renamed it to %s' % (filename,filename +'.processed')
			else:
				os.rename(filename,filename +'.err')
				print '\tError processing %s. File renamed to %s' % (filename,filename +'.err')
	else:
		print '\n** No xml files found to process in %s\n' % (xml_files_path)


###########################################

###########################################

###########################################

###########################################



# Internal Variable initialisations
valid_xml=float(0)
invalid_xml=float(0)

opmn_cmds = ['coreapplication_obips1' ,'coreapplication_obis1','opmn']
#opmn_cmds = ['coreapplication_obips2' ,'coreapplication_obis2','coreapplication_obips1' ,'coreapplication_obis1','opmn']

# OptionParser is depreciated in Python 2.7, but used here for compatibility with Python 2.4 (the version distributed with OEL 5.5)
# NB it does not support newlines (\n) but these are included for when I figure out how to implement them
opts = OptionParser()
opts.description = "obi-metrics-agent will can extract metric data from Fusion MiddleWare (FMW) and its Dynamic Monitoring Systems (DMS).\nIt will poll at a predefined interval and parse the resulting set of metrics.\nThe metrics can be output to a variety of formats, including CSV. Sending to Carbon is also supported, from where graphs can be rendered in Graphite."
# epilog doesn't display, why?
opts.epilog = ("Developed by @rmoff / Rittman Mead (http://www.rittmanmead.com)           Absolutely no warranty, use at your own risk                                         Please include this notice in any copy or reuse of the script you make ")
opts.add_option("-o","--output",action="store",dest="outputformat",default="csv",help="The output format(s) of data, comma separated. More than one can be specified.\nUnparsed options: raw, xml\nParsed options: csv , carbon, sql")
opts.add_option("-d","--data-directory",action="store",dest="DATA",default="./data",help="The directory to which data files are written. Not needed if sole output is carbon.")
opts.add_option("-p","--parse-only",action="store_true",dest="parse_only",default=False, help="If specified, then all raw and xml files specified in the data-directory will be processed, and output to the specified format(s)\nSelecting this option will disable collection of metrics.")
opts.add_option("--fmw-instance",action="store",dest="FMW_INSTANCE",help="Optional. The name of a particular FMW instance. This will be prefixed to metric names.")
opts.add_option("--carbon-server",action="store",dest="CARBON_SERVER",help="The host or IP address of the Carbon server. Required if output format 'carbon' specified.")
opts.add_option("--carbon-port",action="store",dest="CARBON_PORT",default=2003,help="Alternative carbon port, if not 2003.")
opts.add_option("-i","--interval",action="store",dest="interval",default=5,help="The interval in seconds between metric samples.")
opts.add_option("--opmnbin",action="store",dest="OPMN_BIN",help="The complete path to opmnctl. Watch out for spaces.")

input_opts , args = opts.parse_args()

try:
	interval = int(input_opts.interval)
	output=input_opts.outputformat
	parse_only= input_opts.parse_only
	DATA = input_opts.DATA
	FMW_INSTANCE = input_opts.FMW_INSTANCE
	CARBON_SERVER = input_opts.CARBON_SERVER
	CARBON_PORT = int(input_opts.CARBON_PORT)
	OPMN_BIN = input_opts.OPMN_BIN
except Exception, err:
	sys.stderr.write('\t**Error reading input options: %s\n' % str(err))
	sys.exit()

if FMW_INSTANCE is not None:
	FMW_INSTANCE = FMW_INSTANCE.upper()

# For several of the variables, it would be good to fall back on the environment variable if it exists. Maybe put the env var check before the add_option and use the env var if it exists as the default= value

# If OPMN_BIN isn't specified, then try and check the environment variables
if not parse_only:
	if OPMN_BIN is None: 
		try:
			OPMN_BIN = os.environ['OPMN_BIN']
		except:
			# Try a default path
			OPMN_BIN = '/u01/app/oracle/product/fmw/instances/instance1/bin/opmnctl'
			if not os.path.isfile(OPMN_BIN):
				print 'OPMN_BIN must be defined as an environment variable.\nIt can alternatively be specified by the command line parameter --opmnbin.'
				print '\nSet manually, or update setEnv.sh and run it (. ./setEnv.sh)'
				print '*** Exiting ***'
				sys.exit()
	else:
		if os.path.isdir(OPMN_BIN):
			OPMN_BIN = OPMN_BIN + '/opmnctl'
do_output_raw = (output.find('raw') > -1)
do_output_csv = (output.find('csv') > -1)
do_output_xml = (output.find('xml') > -1)
do_output_carbon= (output.find('carbon') > -1)
do_output_sql= (output.find('sql') > -1)

if do_output_carbon and (CARBON_SERVER is None):
	sys.stderr.write('\n\t** Carbon server must be specified if carbon output is selected. \n\tUse --carbon-server and optionally --carbon-port (defaults to 2003)\n\n')
	sys.exit()

# Print header and variable states
print '\n\n\t\tobi-metrics-agent.py\n\n\n'
print '# ==================================================================='
print '# Developed by @rmoff / Rittman Mead (http://www.rittmanmead.com)'
print '# Absolutely no warranty, use at your own risk'
print '# Please include this notice in any copy or reuse of the script you make'
print '# ==================================================================='
print '\n\n---------------------------------------'
print 'Output format             : %s' % output
print 'raw/csv/xml/carbon/sql    : %s/%s/%s/%s/%s' % (do_output_raw,do_output_csv,do_output_xml,do_output_carbon,do_output_sql)
print 'Data dir                  : %s' % DATA
print 'FMW instance              : %s' % FMW_INSTANCE
print 'OPMN BIN                  : %s' % OPMN_BIN
if do_output_carbon:
	print 'Carbon server             : %s' % CARBON_SERVER
	print 'Carbon port               : %d' % CARBON_PORT
if parse_only:
	print '\n\nOption parse_only selected, so no metrics will be gathered. \nThe program will process all data files (xml and raw), and then exit'
else:
	print 'Sample interval (seconds) : %d' % interval
print '---------------------------------------\n'

if not os.path.exists(DATA):
	print '\n\t%s does not exist ... creating' % (DATA)
	os.makedirs(DATA)

# Check process list for collectl?
# print '\n\n   **Don''t forget to start collectl**'

if parse_only:
	parse_files()
else:
	collect_metrics()
