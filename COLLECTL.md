# Install collectl

	sudo yum install -y collectl

Once installed, you can enter `collectl` to run it interactively, but we want to configure it as a daemon (background process) to continually send OS data to graphite/carbon. To do this: 

1. Amend the collectl configuration file

		sudo sed -i.bak -e 's/DaemonCommands/#DaemonCommands/g' /etc/collectl.conf
		sudo sed -i -e '/DaemonCommands/a DaemonCommands = -f \/var\/log\/collectl -P -m -scdmnCDZ --export graphite,localhost:2003,p=.os.,s=cdmnCDZ' /etc/collectl.conf

	Optionally, set to collect every five seconds: 

		sudo sed -i -e '/#Interval =     10/a Interval = 5' /etc/collectl.conf

2. Set `collectl` to start automatically at boot time

	sudo chkconfig --level 35 collectl on

To start collectl as a daemon manually: 

	sudo service collectl start



