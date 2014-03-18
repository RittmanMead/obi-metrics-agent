# Installing Graphite on OEL5 / CentOS 5 / RHEL 5

## Assumptions

1. Installation path is `/home/oracle/graphite`
2. User has **sudo** rights

## yum - package manager

**yum** is the package manager on OEL/CentOS/RHEL that can be used to install software and libraries not already present. The alternative is manually downloading binaries or compiling from source which typically is not a good use of time.

To get **yum** in the state we need it for actually installing graphite, one or two things may need doing on your server first. 

### Fix yum on SampleApp

SampleApp (v309R2) is shipped with **yum** configured to use an internal Oracle proxy. Unless you are on the Oracle network, this causes `yum` to fall in a spectacular heap with errors: 

	Loaded plugins: rhnplugin, security
	This system is not registered with ULN.
	You can use up2date --register to register.
	ULN support will be disabled.
	http://archive.cloudera.com/cdh4/redhat/5/x86_64/cdh/4.2.0/repodata/repomd.xml: [Errno 4] IOError: <urlopen error (-2, 'Name or service not known')>
	Trying other mirror.
	http://public-yum.oracle.com/repo/EnterpriseLinux/EL5/addons/x86_64/repodata/repomd.xml: [Errno 4] IOError: <urlopen error (-2, 'Name or service not known')>
	Trying other mirror.
	http://public-yum.oracle.com/repo/OracleLinux/OL5/latest/x86_64/repodata/repomd.xml: [Errno 4] IOError: <urlopen error (-2, 'Name or service not known')>
	Trying other mirror.
	http://public-yum.oracle.com/repo/OracleLinux/OL5/6/base/x86_64/repodata/repomd.xml: [Errno 4] IOError: <urlopen error (-2, 'Name or service not known')>
	Trying other mirror.

To fix this, remove the `proxy` setting in `/etc/yum.conf` either manually, or by running the following: 

	sudo sed -i.bak -e 's/proxy=/#proxy=/g' /etc/yum.conf

Conversely, if you are on a network where `yum` needs to use a proxy, here is where you can configure it :-)

### Install the EPEL yum repository

Several packages used for setting up the environment (eg. git, libffi, virtualenv) are in the **Extra Packages for Enterprise Linux** (EPEL) repository, so you need to add this to the `yum` repository list first. Do this as follows: 

	cd /tmp
	wget http://mirror.bytemark.co.uk/fedora/epel/5/i386/epel-release-5-4.noarch.rpm
	sudo rpm -i epel-release-5-4.noarch.rpm
	rm epel-release-5-4.noarch.rpm
	
## Install dependencies

	sudo yum install -y python26-devel bitmap-fonts httpd python26-mod_wsgi mod_python26 git python26-virtualenv cairo-devel libffi libffi-devel
	virtualenv-2.6 -p python2.6 /home/oracle/graphite
	cat>>/home/oracle/graphite/bin/activate<<EOF
	export PYTHONPATH=/home/oracle/graphite/lib/python2.6/site-packages/
	EOF
	source /home/oracle/graphite/bin/activate
	pip install django django-tagging 'Twisted<12.0' pyparsing pytz cairocffi
	#
	# Needs compiling from source
	mkdir /home/oracle/zope-src/
	cd /home/oracle/zope-src/
	wget --no-check-certificate https://pypi.python.org/packages/source/z/zope.interface/zope.interface-4.1.0.tar.gz#md5=ac63de1784ea0327db876c908af07a94
	tar xf zope.interface-4.1.0.tar.gz
	cd zope.*
	python setup.py install --install-lib=/home/oracle/graphite/lib/python2.6/site-packages

## Download graphite and supporting software

These will be compiled from source

	cd /home/oracle
	git clone https://github.com/graphite-project/graphite-web.git 
	git clone https://github.com/graphite-project/carbon.git 
	git clone https://github.com/graphite-project/whisper.git 
	git clone https://github.com/graphite-project/ceres.git 

## Compile graphite and supporting software

	cd /home/oracle/graphite-web && python26 setup.py install --prefix=/home/oracle/graphite --install-lib=/home/oracle/graphite/lib
	cd /home/oracle/carbon && python26 setup.py install --prefix=/home/oracle/graphite --install-lib=/home/oracle/graphite/lib
	sudo cp distro/redhat/init.d/carbon-cache /etc/init.d
	cd /home/oracle/whisper && python26 setup.py install --prefix=/home/oracle/graphite --install-lib=/home/oracle/graphite/lib
	cd /home/oracle/ceres && python26 setup.py install --prefix=/home/oracle/graphite --install-lib=/home/oracle/graphite/lib
	# Doesn't get created by git install
	mkdir -p /home/oracle/graphite/storage/log/carbon-cache/carbon-cache-a  

## Configure Carbon (graphite's storage engine)

	cd /home/oracle/graphite/conf/
	cp carbon.conf.example carbon.conf
	sed -i -e 's/MAX_CREATES_PER_MINUTE = 50/MAX_CREATES_PER_MINUTE = inf/' carbon.conf
	# Defaults to 7002, which is also the AdminServer SSL port so may well be taken.
	sed -i -e 's/CACHE_QUERY_PORT = 7002/CACHE_QUERY_PORT = 17002/' carbon.conf
	# Create storage-schemas.conf
	cat>storage-schemas.conf<<EOF
	[default_5sec_for_14day]
	pattern = .*
	retentions = 5s:14d
	EOF

## Start carbon cache

	# If this is outside the original install session, you'll need to run the "source" command again
	source /home/oracle/graphite/bin/activate
	cd /home/oracle/graphite/
	./bin/carbon-cache.py start

Confirm carbon cache is indeed now running: 

	./bin/carbon-cache.py status

If it's not, check in `/home/oracle/graphite/storage/log/carbon-cache/carbon-cache-a` for errors

## Set up graphite web application in Apache

	sudo cp /home/oracle/graphite/examples/example-graphite-vhost.conf /etc/httpd/conf.d/graphite-vhost.conf
	sudo sed -i -e 's/WSGISocketPrefix.*$/WSGISocketPrefix \/etc\/httpd\/wsgi\//' /etc/httpd/conf.d/graphite-vhost.conf
	sudo sed -i -e 's/\/opt\/graphite/\/home\/oracle\/graphite/' /etc/httpd/conf.d/graphite-vhost.conf
	sudo sed -i -e 's/modules\/mod_wsgi.so/modules\/python26-mod_wsgi.so/' /etc/httpd/conf.d/graphite-vhost.conf
	sudo mkdir -p /etc/httpd/wsgi
	cp /home/oracle/graphite/conf/graphite.wsgi.example /home/oracle/graphite/conf/graphite.wsgi
	# This needs to match whatever --install-lib was set to when running setup.py install for graphite-web 
	sed -i -e 's/\/opt\/graphite\/webapp/\/home\/oracle\/graphite\/lib/' /home/oracle/graphite/conf/graphite.wsgi
	sed -i -e "/^sys.path.append/a sys.path.append('\/home\/oracle\/graphite\/lib\/python2.6\/site-packages\/')"  /home/oracle/graphite/conf/graphite.wsgi

	# Frig permissions so apache can access the webapp
	chmod o+rx /home/oracle
	chmod -R o+rx /home/oracle/graphite

## Set graphite web app settings

	# This needs to match whatever --install-lib was set to when running setup.py install for graphite-web
	cd /home/oracle/graphite/lib/graphite
	cp local_settings.py.example local_settings.py
	sed -i -e "/TIME_ZONE/a TIME_ZONE = \'Europe\/London\'" local_settings.py
	sed -i -e "s/#SECRET_KEY/SECRET_KEY/" local_settings.py
	sed -i -e "s/#GRAPHITE_ROOT.*$/GRAPHITE_ROOT = '\/home\/oracle\/graphite'/" local_settings.py

	cat >> local_settings.py<<EOF
	DATABASES = {
	    'default': {
		'NAME': '/home/oracle/graphite/storage/graphite.db',
		'ENGINE': 'django.db.backends.sqlite3',
		'USER': '',
		'PASSWORD': '',
		'HOST': '',
		'PORT': ''
	    }
	}
	EOF

## Set up graphite backend datastore

	PYTHONPATH=/home/oracle/graphite/lib/ /home/oracle/graphite/bin/django-admin.py syncdb --settings=graphite.settings

* Enter 'yes' when prompted to create a superuser. 
* Leave username & email address blank
* Enter a new password for the root graphite user (make a note of it)

## Start Apache

The first time after running the setup step above (`django-admin.py`) you need to fix the permissions once more: 

	chmod -R o+rwx /home/oracle/graphite

and you can then [re]start apache, the web server for graphite: 

	sudo service httpd restart

You should now be able to go to `http://<server>/graphite` and see the initial graphite web page.