import time
from functions_core import secure_connect, netcat
import re
import logging
import threading

def func_eternus_icp_fs(args):

    # Get variables from args
    param_ip=args[0]
    param_system_name=args[1]
    param_alias=args[2]
    user=args[3]
    host_keys=args[4]
    known_hosts=args[5]
    bastion=args[6]
    use_sudo=args[7]
    PLATFORM_REPO=args[8]
    PLATFORM_REPO_PORT=args[9]
    PLATFORM_REPO_PROTOCOL=args[10]

    logging.info("Starting func_eternus_icp_fs on thread %s wth args %s - %s" % (threading.current_thread(),args,time.ctime()))

    # Command line to run remotly
    CMD1="/opt/fsc/CentricStor/bin/rdNsdInfos -a > /tmp/stats_nsd.out"
    CMD2="/usr/bin/iostat -x -k 1 2| awk '!/^sd/'|awk -vN=2 '/avg-cpu/{++n} n>=N' > /tmp/stats_iostat.out"
    CMD3="awk \'NR==FNR{a[$1]=$0; next} $3 in a{print a[$3],$0}\' /tmp/stats_iostat.out /tmp/stats_nsd.out | awk '{print $18\" \"$1\" \"$2\" \"$3\" \"$4\" \"$5\" \"$6\" \"$7\" \"$8 \" \"$9\" \"$10\" \"$11\" \"$12\" \"$13\" \"$14\" \"$15\" \"$16\" \"$17}' | sort"
    
    logging.debug("use_sudo is set to %s" % use_sudo)
    
    if use_sudo is True:
        CMD1 = "sudo " + CMD1
        logging.debug("Will use CMD1 with sudo - %s" % CMD1)
    
    logging.debug("Command Line 1 - %s" % CMD1)
    logging.debug("Command Line 2 - %s" % CMD2)
    logging.debug("Command Line 3 - %s" % CMD3)



#    ssh.run(CMD1)
#    ssh.run(CMD2)
#    stdout = ssh.run(CMD3, hide=True)
#    timestamp = int(time.time())
#    response = stdout.stdout
#    logging.debug("Output of Command Line 3 - %s" % response)
#    logging.info("Finished ssh execution to get metrics - %s" % time.ctime())
#    for line in response.splitlines():
#        if len(line.split())==18 and not line.startswith("\n") and not line.startswith("Device"):
#            logging.info("Starting metrics processing on FS type - %s" % time.ctime())
#            columns = line.split()
#            netcat(PLATFORM_REPO, PLATFORM_REPO_PORT, PLATFORM_REPO_PROTOCOL,  str(PLATFORM) + "." + str(PLATFORM_NAME) + "." + str(type) + "." + hostname.replace(".","-") + "." + "fs" + str(columns[0]) + "." + str(columns[1]) + "." + str(columns[17]) + "." + "svctm" + " " + re.sub(",",".",columns[15]) +" "+ str(timestamp) + "\n")
#            netcat(PLATFORM_REPO, PLATFORM_REPO_PORT, PLATFORM_REPO_PROTOCOL,  str(PLATFORM) + "." + str(PLATFORM_NAME) + "." + str(type) + "." + hostname.replace(".","-") + "." + "fs" + str(columns[0]) + "." + str(columns[1]) + "." + str(columns[17]) + "." + "%util" + " " + re.sub(",",".",columns[16]) +" "+ str(timestamp) + "\n")
#            logging.info("Finished metrics processing on FS type - %s" % time.ctime())