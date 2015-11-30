import getopt
import sys

def printUsage():
#	print """
#      _    _               _       _                             _   
#  ___| |__(_)___ _ __  ___| |_ _ _(_)__ ______ __ _ __ _ ___ _ _| |_ 
# / _ \ '_ \ |___| '  \/ -_)  _| '_| / _(_-<___/ _` / _` / -_) ' \  _|
# \___/_.__/_|   |_|_|_\___|\__|_| |_\__/__/   \__,_\__, \___|_||_\__|
#                                                   |___/             
#
#"""
	print ' '
	print '                    obi-metrics-agent'
	print '                    -----------------'
	print '                               @rmoff'
	print ' '
	print 'Usage:'
	print '  $FMW_HOME/oracle_common/common/bin/wlst.sh obi-metrics-agent.py <options>'
	print ' '
	print 'Options:'
	print """
  --debug		Enable debug output
  --stdout		Output data to stdout, in tab-separated form
  --env-label		Optional arbitrary label for the environment's data. Useful when 
			multiple environments run on the same host and the host name alone would
			not uniquely identify the data collected.

  --temp		Get OBIEE Temp usage on disk by component
  --fmwHome		Fusion Middleware Home folder. Mandatory if collection temp stats. Not required otherwise.
  --fmwInstance		Fusion Middleware instance. Used for temp stats monitoring. Defaults to instance1

  --dms			Get DMS metrics
  --wls-admin		The Admin user for WLS (often weblogic)
  --wls-pw		The password for the admin user on WLS 
  --wls-url		The URL of the WLS Admin Server. Defaults to t3://localhost:7001

  --influx-host		The host of the InfluxDB server. If specified, data will be sent to InfluxDB.
  --influx-port		The port of the InfluxDB server. Defaults to 8086.
  --influx-db		The database in InfluxDB to write to. Defaults to obi.

  --es-host		The host of the Elasticsearch server. If specified, data will be sent to Elasticsearch.
  --es-port		The port of the Elasticsearch server. Defaults to 9200.
  --es-index		The index in Elasticsearch to write to. Defaults to obi.
	"""
	print ' '

debug=False
env_label=None
do_dms=False
do_temp=False
wls_url='t3://localhost:7001'
influx_port=8086
influx_db='obi'
es_port=9200
es_index='obi'
fmwHome=None
wls_admin=None
wls_pw=None
stdout=None
influx_host=None
es_host=None

try:
	options,remainder = getopt.getopt(sys.argv[1:],'', ['dms', 'temp', 'fmwHome=', 'env-label=','wls-admin=', 'wls-pw=', 'wls-url=', 'stdout=', 'influx-host=', 'influx-port=', 'influx-db=', 'es-host=', 'es-port=', 'es-index=','debug'])
except getopt.error, msg:
	printUsage()
	print '**\n**\t%s\n\n' % msg
	sys.exit(2)

for opt, arg in options:
	if opt == '--dms':
		do_dms=True
	elif opt == '--env-label':
		env_label=arg
	elif opt == '--debug':
		debug=True
	elif opt == '--temp':
		do_temp=True
	elif opt == '--fmwHome':
		fmwHome=arg
	elif opt == '--wls-admin':
		wls_admin=arg
	elif opt == '--wls-pw':
		wls_pw=arg
	elif opt == '--wls-url':
		wls_url=arg
	elif opt == '--stdout':
		stdout=arg
	elif opt == '--influx-host':
		influx_host=arg
	elif opt == '--influx-port':
		influx_port=arg
	elif opt == '--influx-db':
		influx_db=arg
	elif opt == '--es-host':
		es_host=arg
	elif opt == '--es-port':
		es_port=arg
	elif opt == '--es-index':
		es_index=arg

if do_temp:
	if fmwHome is None: 
		printUsage()
		print "**\n**\tERROR: If you want to monitor temp usage, you need to specify --fmwHome\n\n"
		sys.exit(2)
if do_dms:
	if (wls_admin is None or wls_pw is None or wls_url is None):
		printUsage()
		print "**\n**\tERROR: If collecting DMS metrics, you must specify wls-admin, wls-pw, and wls-url\n\n"
		sys.exit(2)
	
print wls_admin
print wls_pw
print wls_url
print stdout
print influx_host
print influx_port
print influx_db
print es_host
print es_port
print es_index

