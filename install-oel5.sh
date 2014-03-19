# Fix yum on SampleApp  
sudo sed -i.bak -e 's/proxy=/#proxy=/g' /etc/yum.conf  

# Install the EPEL yum repository  
cd /tmp  
wget http://mirror.bytemark.co.uk/fedora/epel/5/i386/epel-release-5-4.noarch.rpm  
sudo rpm -i epel-release-5-4.noarch.rpm  
rm epel-release-5-4.noarch.rpm  

# Install dependencies  
# Install packages through yum, including python26. This won't overwrite the system's python version, but makes it available for use.   
sudo yum install -y python26-devel bitmap-fonts httpd python26-mod_wsgi mod_python26 git python26-virtualenv cairo-devel libffi libffi-devel  

# Using virtualenv, create a standalone Python 2.6 environment in which Graphite will run  
virtualenv-2.6 -p python2.6 /home/oracle/graphite  
cat>>/home/oracle/graphite/bin/activate<<EOF  
export PYTHONPATH=/home/oracle/graphite/lib/python2.6/site-packages/  
EOF  
source /home/oracle/graphite/bin/activate  

# Install Python libraries  
pip install django django-tagging 'Twisted<12.0' pyparsing pytz cairocffi  

# Compile zope from source  
mkdir /home/oracle/zope-src/  
cd /home/oracle/zope-src/  
wget --no-check-certificate https://pypi.python.org/packages/source/z/zope.interface/zope.interface-4.1.0.tar.gz#md5=ac63de1784ea0327db876c908af07a94  
tar xf zope.interface-4.1.0.tar.gz  
cd zope.*  
python setup.py install --install-lib=/home/oracle/graphite/lib/python2.6/site-packages  

# Download and compile graphite and supporting components  
cd /home/oracle  
git clone https://github.com/graphite-project/graphite-web.git   
git clone https://github.com/graphite-project/carbon.git   
git clone https://github.com/graphite-project/whisper.git   
git clone https://github.com/graphite-project/ceres.git   


cd /home/oracle/graphite-web && python26 setup.py install --prefix=/home/oracle/graphite --install-lib=/home/oracle/graphite/lib  
cd /home/oracle/carbon && python26 setup.py install --prefix=/home/oracle/graphite --install-lib=/home/oracle/graphite/lib  
cd /home/oracle/whisper && python26 setup.py install --prefix=/home/oracle/graphite --install-lib=/home/oracle/graphite/lib  
cd /home/oracle/ceres && python26 setup.py install --prefix=/home/oracle/graphite --install-lib=/home/oracle/graphite/lib  

# Two manual steps  
mkdir -p /home/oracle/graphite/storage/log/carbon-cache/carbon-cache-a    
sudo cp /home/oracle/carbon/distro/redhat/init.d/carbon-cache /etc/init.d  

# Configure Carbon (graphite's storage engine)  
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

# Start carbon cache  
# If this is outside the original install session, you'll need to run the "source" command again  
source /home/oracle/graphite/bin/activate  
cd /home/oracle/graphite/  
./bin/carbon-cache.py start  

# Set up graphite web application in Apache  

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

# Set graphite web app settings  

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

# Set up graphite backend datastore  

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

# Start Apache  

chmod -R o+rwx /home/oracle/graphite  
sudo service httpd restart  

echo 'You should now be able to go to one of the following IPs to see the initial graphite web page'   
echo $(ip a|grep inet|grep -v 127.0.0.1|awk '{gsub("/24","");print "http://"$2}')

