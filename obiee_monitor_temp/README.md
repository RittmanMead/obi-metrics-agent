obiee_temp_monitor
===

# Overview

This script will record the amount of temporary space used on disk by the OBIEE system components. It writes it to a TSV file, which can then be loaded to Oracle DB using the provided SQL*Loader script. 

# Configuration

This assumes that you have one or more OBIEE/FMW installations on the server, and that they are under a common parent of $FMW_BASE. 
One output file will be written per FMW installation. The assumption is that the data pertaining to each installation will be written to its own Oracle schema. 

Edit the files as follows: 

## obiee_monitor_temp.sh

* Set `FMW_BASE` to the parent folder of all FMW installs, eg, `/oracle`

* Set `OUT_BASE` to the path where you want to write the temporary output from the script prior to it being loaded to Oracle. The actual filenames written to will use OUT_BASE as the prefix to environment-specific names. 

## obiee_monitor_temp.sql

Edit the schema prefix on this to that of the environment(s) schemas that will be written to. For multiple environments, clone and edit this file once per environment accordingly. 

Once updated, run this whole SQL script to create the base table and dependent view.

## obiee_monitor_temp.ctl

* Using the provided `.sample`, create a version of this file for each environment for which temp files are being monitored. 

* Update the prefix on `INFILE`, `BADFILE`, `DISCARDFILE` from `/tmp` to match  that specified as `OUT_BASE` above

* Update `ENV` in the filename to match that of the FMW home environment name (picked up from the folder name under `FMW_BASE`)

* Update the schema owner as required

## obiee_monitor_temp_load_table.sh

* Using the provided `.sample`, create a version of this file for each environment for which temp files are being monitored. 

* Update the prefix in the `mv` statement from `/tmp` to match that specified as `OUT_BASE` above

* Update `ENV` in the filename to match that of the FMW home environment name (picked up from the folder name under `FMW_BASE`)

* Specify the appropriate userid/password/SID in the `userid` parameter

* Update the `control` parameter filename to match that of the control file created/modified above

## Usage

* Copy `obiee_monitor_temp.sh` to `/etc/init.d` and run `chkconfig obiee_monitor_temp on`
* Schedule a minutely crontab to call `obiee_monitor_temp_load_table.sh` for each environment
