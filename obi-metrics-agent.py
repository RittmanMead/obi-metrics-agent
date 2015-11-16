# obi-metrics-agent.py
#
# Extract DMS metrics from Fusion MiddleWare (FMW)
#
# @rmoff / Rittman Mead
# November 2015
# v2.00
#
# Add to cronab: 
# 0-59 * * * * /app/oracle/biee/oracle_common/common/bin/wlst.sh ~/obi-metrics-agent.py weblogic Admin123 t3://localhost:7001 2>/dev/null 1>&2
#
# TODO: 
#   - Document use
#   - Better command line argument handling (use getopt?)
#   - Add option to repeat loop with sleep, so that can be called from crontab every minute and capture stats at a greater frequency than minute (eg launch with interval of 10, samples 5, to take five samples and then sleep)
#   - Error handling
#   - Get InfluxDB output working as a batch
#   - Make the wlst call not echo to stdout
#   - For writing to InfluxDB, test if the DB exists already and if not create it
#

import calendar, time
import sys
import getopt

print '---------------------------------------'

# Check the arguments to this script are as expected.
# argv[0] is script name.
argLen = len(sys.argv)
if argLen -1 < 2:
	print "ERROR: got ", argLen -1, " args, must be at least two."
 	print '$FMW_HOME/oracle_common/common/bin/wlst.sh obi-metrics-agent.py  <AdminUserName> <AdminPassword> [<AdminServer_t3_url>] [<Carbon|InfluxDB>] [<target host>] [<target port>] [targetDB influx db>'
	exit()

outputFormat='InfluxDB'
url='t3://localhost:7001'
targetHost='localhost'
targetDB='obi'
targetPort='8086'

try:
	wls_user = sys.argv[1]
	wls_pw = sys.argv[2]
	url  = sys.argv[3]
	outputFormat=sys.argv[4]
	targetHost=sys.argv[5]
	targetPort=sys.argv[6]
	targetDB=sys.argv[7]
except:
	print ''

print wls_user, wls_pw,url, outputFormat,targetHost,targetPort,targetDB

if wls_user.isspace():

	print "Error: wls_user argument not found."
	printUsage()
	sys.exit(2)

if wls_pw.isspace():
	print "Error: wls_pw argument not found."
	printUsage()
	sys.exit(2)

if url.isspace():
	print "Warning: url argument not found. Specify it in the format 't3://localhost7001'"

if outputFormat.isspace():
	print "Warning: outputFormat argument not found. Specify Carbon or InfluxDB. Defaulting to InfluxDB"

if targetHost.isspace():
	print "Warning: targetHost argument not found. Specify the host of the Influx/Carbon instance to which the metrics are to be sent. Defaulting to localhost"

if targetPort.isspace():
	print "Warning: targetPort argument not found. Specify the host of the Influx/Carbon instance to which the metrics are to be sent. Defaulting to 8086"

if targetDB.isspace():
	print "Warning: targetDB argument not found. Specify the InfluxDB to which metrics are to be written. Defaulting to obi."

print wls_user, wls_pw,url, outputFormat,targetHost,targetPort,targetDB

now_epoch = calendar.timegm(time.gmtime())*1000
if outputFormat=='Carbon':
	import socket
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
	s.connect((targetHost, targetPort)) 

if outputFormat=='InfluxDB':
	import httplib
	influx_msgs=''

connect(wls_user,wls_pw,url)
results = displayMetricTables('Oracle_BI*','dms_cProcessInfo')
for table in results:
	tableName = table.get('Table')
	rows = table.get('Rows')
	rowCollection = rows.values()
	iter = rowCollection.iterator()
	while iter.hasNext():
		row = iter.next()
		rowType = row.getCompositeType()
		keys = rowType.keySet()
		keyIter = keys.iterator()
		inst_name= row.get('Name').replace(' ','-')
		try:
			server= row.get('Servername').replace(' ','-')
		except:
			server=''
		try:
			host= row.get('Host').replace(' ','-')
		except:
			host=''
		while keyIter.hasNext():
			columnName = keyIter.next()
			value = row.get(columnName )
			if columnName.find('.value')>0:
				metric_name=columnName.replace('.value','')
				if outputFormat=='Carbon':
					carbon_msg= ('%s.%s.%s.%s.%s %s %s') % (host,tableName,inst_name, server,metric_name, value,now_epoch)
					s.send(carbon_msg)
					#print carbon_msg
				if outputFormat=='InfluxDB':
					influx_msg= ('%s,server=%s,host=%s,metric_group=%s,metric_instance=%s value=%s %s') % (metric_name,server,host,tableName,inst_name,  value,now_epoch*1000000)
					influx_msgs+='\n%s' % influx_msg
					conn = httplib.HTTPConnection('%s:%s' % (targetHost,targetPort))
					a=conn.request("POST", ("/write?db=%s" % targetDB), influx_msg)
if outputFormat=='Carbon':
	s.close()
if outputFormat=='InfluxDB':
	print 'TODO: Batch InfluxDB requests into single send - currently done one by one which is inefficient'
	#conn = httplib.HTTPConnection('%s:%s' % (targetHost,targetPort))
	#a=conn.request("POST", ("/write?db=%s" % targetDB), influx_msgs)
