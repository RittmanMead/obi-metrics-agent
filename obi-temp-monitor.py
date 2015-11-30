# obi-temp-monitor.py
#
# Monitor usage of temp files by OBIEE
#
# @rmoff / Rittman Mead
# November 2015
# v0.01
#
# TODO: parse config files to determine the work paths automagically
#
#
# Add to cronab: 
# 0-59 * * * * /app/oracle/biee/oracle_common/common/bin/wlst.sh /path/to/obi-temp-monitor.py 2>/dev/null 1>&2
#
# TODO: 
#   - Document use
#   - Add debug flag
#   - Better command line argument handling (use getopt?)
#   - Add option to repeat loop with sleep, so that can be called from crontab every minute and capture stats at a greater frequency than minute (eg launch with interval of 10, samples 5, to take five samples and then sleep)
#   - Error handling
#   - Get InfluxDB output working as a batch
#   - For writing to InfluxDB, test if the DB exists already and if not create it
#

import os
import calendar, time
import sys
import socket

def get_size(dirname):
  size=0
  #print 'A-%s\t%s' % (size,dirname)
  for name in os.listdir(dirname):
    #print '\t%s' % name
    path = os.path.join(dirname, name)
    this_size=os.stat(path).st_size
    size+=this_size
    if os.path.isdir(path):
      size+=get_size(path)
  #print 'B-%s\t%s' % (size,dirname)
  return size


outputFormat='InfluxDB'
targetHost='localhost'
targetDB='obi_temp'
targetPort='8086'
instance='instance1'
env='TEST'

try:
	fmwHome=sys.argv[1]
	outputFormat=sys.argv[2]
	targetHost=sys.argv[3]
	targetPort=sys.argv[4]
	targetDB=sys.argv[5]
	env=sys.argv[6]
except:
	print ''

if fmwHome.isspace():
	print "ERROR: fmwHome argument not found. "
 	print '  Usage: $FMW_HOME/oracle_common/common/bin/wlst.sh obi-temp-monitor.py $FMW_HOME [<Carbon|InfluxDB>] [<target host>] [<target port>] [targetDB influx db] [env descriptor]'
	sys.exit(1)

if outputFormat.isspace():
	print "Warning: outputFormat argument not found. Specify Carbon or InfluxDB. Defaulting to InfluxDB"
 	print '  Usage: $FMW_HOME/oracle_common/common/bin/wlst.sh obi-temp-monitor.py $FMW_HOME [<Carbon|InfluxDB>] [<target host>] [<target port>] [targetDB influx db] [env descriptor]'
else:
	if outputFormat == 'InfluxDB':
		if targetHost.isspace():
			print "Warning: targetHost argument not found. Specify the host of the Influx/Carbon instance to which the metrics are to be sent. Defaulting to localhost"
			print '  Usage: $FMW_HOME/oracle_common/common/bin/wlst.sh obi-temp-monitor.py $FMW_HOME [<Carbon|InfluxDB>] [<target host>] [<target port>] [targetDB influx db] [env descriptor]'

		if targetPort.isspace():
			print "Warning: targetPort argument not found. Specify the host of the Influx/Carbon instance to which the metrics are to be sent. Defaulting to 8086"
			print '  Usage: $FMW_HOME/oracle_common/common/bin/wlst.sh obi-temp-monitor.py $FMW_HOME [<Carbon|InfluxDB>] [<target host>] [<target port>] [targetDB influx db] [env descriptor]'

		if targetDB.isspace():
			print "Warning: targetDB argument not found. Specify the InfluxDB to which metrics are to be written. Defaulting to obi."
			print '  Usage: $FMW_HOME/oracle_common/common/bin/wlst.sh obi-temp-monitor.py $FMW_HOME [<Carbon|InfluxDB>] [<target host>] [<target port>] [targetDB influx db] [env descriptor]'

if env.isspace():
	print "Info: env argument not found. This is an optional argument that can be specified when multiple environments are running on the same host."
 	print '  Usage: $FMW_HOME/oracle_common/common/bin/wlst.sh obi-temp-monitor.py $FMW_HOME [<Carbon|InfluxDB>] [<target host>] [<target port>] [targetDB influx db] [env descriptor]'


now_epoch = calendar.timegm(time.gmtime())*1000
host=socket.gethostname()

if outputFormat=='InfluxDB':
	import httplib
	influx_msgs=''
if outputFormat=='tsv':
	f = open('/tmp/obi_temp_usage.tsv','w')

temp_folders=os.path.join(fmwHome,'instances',instance,'tmp')
for server in os.listdir(temp_folders):
	path=os.path.join(temp_folders,server)
	#print path
	if os.path.isdir(path):
		#print server
		bytes = get_size(path)
		#print bytes
		if outputFormat=='InfluxDB':
			if env:
				influx_msg= ('AppTempBytes,environment=%s,server=%s,host=%s value=%s %s') % (env,server,host, bytes,now_epoch*1000000)
			else:
				influx_msg= ('AppTempBytes,server=%s,host=%s value=%s %s') % (server,host, bytes,now_epoch*1000000)
			#print influx_msg
			influx_msgs+='\n%s' % influx_msg
			conn = httplib.HTTPConnection('%s:%s' % (targetHost,targetPort))
			a=conn.request("POST", ("/write?db=%s" % targetDB), influx_msg)

		if outputFormat=='tsv':
			if env:
				tsv_msg= ('%s\t%s\t%s\t%s\t%s') % (now_epoch,server,host, bytes)
			else:
				tsv_msg= ('%s\t%s\t%s\t%s') % (now_epoch,server,host, bytes)
			f.write(tsv_msg)

if outputFormat=='tsv':
	f.close()

