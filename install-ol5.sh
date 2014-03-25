# Set up EPEL
sudo rpm -Uvh http://dl.fedoraproject.org/pub/epel/5/i386/epel-release-5-4.noarch.rpm
# Install LXML etc
sudo yum install -y libxslt-devel python-setuptools git
sudo easy_install lxml

# Install Graphite
./install-graphite-ol5.sh

# Install and configure collectl
sudo yum install -y collectl
sudo chkconfig --level 35 collectl on
sudo sed -i.bak -e 's/DaemonCommands/#DaemonCommands/g' /etc/collectl.conf
sudo sed -i -e '/DaemonCommands/a DaemonCommands = -f \/var\/log\/collectl -P -m -scdmnCDZ --export graphite,localhost:2003,p=.os.,s=cdmnCDZ' /etc/collectl.conf
sudo sed -i -e '/#Interval =     10/a Interval = 5' /etc/collectl.conf
sudo service collectl restart
