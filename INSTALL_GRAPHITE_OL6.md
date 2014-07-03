# Automagic installation of Graphite on OL 6 / CentOS 6 / RHEL 6

You can either run the installation interactively, following the steps and explanations below, or download the full script to do it all automagically. 

Regardless of the method chosen, there are some important assumptions made: 

1. Server has internet access (try `ping google.com` to check)
2. Installation is running as the `oracle` user
1. Installation path is `/home/oracle/graphite`
2. User has **sudo** rights

**To download and run the automagic install script**, enter: 

	wget --no-check-certificate https://raw.github.com/RittmanMead/obi-metrics-agent/master/install-ol6.sh
	chmod u+x ./install-ol6.sh
	./install-ol6.sh
	
This will do all the necessary setup for graphite. It will take about five minutes to run. Once complete, go to `http://<server>` in your web browser to see the initial graphite page. 

# Step by step installation

## yum - package manager

**yum** is the package manager on OL/CentOS/RHEL that can be used to install software and libraries not already present. The alternative is manually downloading binaries or compiling from source which typically is not a good use of time.

To get **yum** in the state we need it for actually installing graphite, one or two things may need doing on your server first. 

### Install the EPEL yum repository

Several packages used for setting up the environment (eg. git, libffi, virtualenv) are in the **Extra Packages for Enterprise Linux** (EPEL) repository, so you need to add this to the `yum` repository list first. Do this as follows: 

	sudo rpm -Uvh http://dl.fedoraproject.org/pub/epel/6/`uname -p`/epel-release-6-8.noarch.rpm
	
## Install dependencies

This will use `yum` to download necessary packages. 

It then builds a standalone **python** environment using `virtualenv` in which graphite will run. This keeps graphite nicely isolated from other python components on the server. 

Once the Python environment is set up, `pip` is used to install required Python libraries, and finally `zope` is downloaded and compiled manually. This last step was necessary to meet the dependency requirement that Graphite has and couldn't be met with the usual `pip` installation route.

	# Install packages through yum
	sudo yum install -y python-pip python-devel pycairo-devel bitmap-fonts httpd mod_wsgi mod_python git python-virtualenv libffi libffi-devel

	# Using virtualenv, create a standalone environment in which Graphite will run
	virtualenv /home/oracle/graphite
	source /home/oracle/graphite/bin/activate
	
	# Install Python libraries
	pip install django django-tagging 'Twisted<12.0' pyparsing pytz cairocffi

## Download and compile graphite and supporting components

Graphite can be installed using `pip` but I found better results by downloading and compiling from source

	cd /home/oracle
	git clone https://github.com/graphite-project/graphite-web.git 
	git clone https://github.com/graphite-project/carbon.git 
	git clone https://github.com/graphite-project/whisper.git 
	git clone https://github.com/graphite-project/ceres.git 


	cd /home/oracle/graphite-web && python setup.py install --prefix=/home/oracle/graphite --install-lib=/home/oracle/graphite/lib
	cd /home/oracle/carbon && python setup.py install --prefix=/home/oracle/graphite --install-lib=/home/oracle/graphite/lib
	cd /home/oracle/whisper && python setup.py install --prefix=/home/oracle/graphite --install-lib=/home/oracle/graphite/lib
	cd /home/oracle/ceres && python setup.py install --prefix=/home/oracle/graphite --install-lib=/home/oracle/graphite/lib

	# Two manual steps
	mkdir -p /home/oracle/graphite/storage/log/carbon-cache/carbon-cache-a  
	sudo cp /home/oracle/carbon/distro/redhat/init.d/carbon-cache /etc/init.d

Enable carbon-cache to start at bootup

	sed -i -e 's/^GRAPHITE_DIR.*$//g' /home/oracle/carbon/distro/redhat/init.d/carbon-cache
	sed -i -e '/export PYTHONPATH/i export GRAPHITE_DIR="\/home\/oracle\/graphite"' /home/oracle/carbon/distro/redhat/init.d/carbon-cache
	sed -i -e 's/chkconfig.*$/chkconfig: 345 95 20/g' /home/oracle/carbon/distro/redhat/init.d/carbon-cache

	sudo cp /home/oracle/carbon/distro/redhat/init.d/carbon-cache /etc/init.d
	sudo chmod 750 /etc/init.d/carbon-cache
	sudo chkconfig --add carbon-cache

Tidy up by removing the original git repositories from which the software was built

	cd /home/oracle
	rm -rf carbon/ graphite-web/ whisper/

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

	# Credit for making this non-interactive: http://obfuscurity.com/2012/04/Unhelpful-Graphite-Tip-4
	# Ref: https://docs.djangoproject.com/en/dev/howto/initial-data/
	
	# Create the initial_data.json file, holding our superuser details 
	# (extracted from a manual install using django-admin.py dumpdata auth.User)
	# Login : oracle / Password01
	# (the backslash before the EOF means the special characters in the password hash etc are treated as literals)
	cat>/home/oracle/graphite/lib/initial_data.json<<\EOF
	[{"pk": 1, "model": "auth.user", "fields": {"username": "oracle", "first_name": "", "last_name": "", "is_active": true, "is_superuser": true, "is_staff": true, "last_login": "2014-03-19T09:22:11.263", "groups": [], "user_permissions": [], "password": "pbkdf2_sha256$12000$jFHXs0bYKO00$IvHMuDUdsvuRxWqaAuXPAhcB/FG4NTBdrVspsyWe5h8=", "email": "", "date_joined": "2014-03-13T21:07:14.276"}}, {"pk": 2, "model": "auth.user", "fields": {"username": "default", "first_name": "", "last_name": "", "is_active": true, "is_superuser": false, "is_staff": false, "last_login": "2014-03-13T21:16:37.958", "groups": [], "user_permissions": [], "password": "!", "email": "default@localhost.localdomain", "date_joined": "2014-03-13T21:16:37.958"}}]
	EOF
	
	# Initalise the database
	# The initial_data.json is read from $PWD (or /home/oracle/graphite/lib/python2.6/site-packages/django/contrib/auth/fixtures but that wouldn't be right)
	cd /home/oracle/graphite/lib/
	PYTHONPATH=/home/oracle/graphite/lib/ /home/oracle/graphite/bin/django-admin.py syncdb --noinput --settings=graphite.settings --verbosity=3

## Start Apache

The first time after running the setup step above (`django-admin.py`) you need to fix the permissions once more: 

	chmod -R o+rwx /home/oracle/graphite

and you can then [re]start apache, the web server for graphite: 

	sudo service httpd restart

You should now be able to go to `http://<server>` and see the initial graphite web page.

