source /home/oracle/.bash_profile
mv --no-clobber /u01/data/obi-temp/obiee.biee.du.tsv /u01/data/obi-temp/obiee.biee.du.tsv.stage && sqlldr userid=biee_biplatform/Oracle123@pdborcl control=/opt/obi-metrics-agent/obiee_monitor_temp/obiee_monitor_temp.ctl && rm /u01/data/obi-temp/obiee.biee.du.tsv.stage
