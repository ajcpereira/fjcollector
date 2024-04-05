import os, logging, subprocess, time, re
import pandas as pd
from functions_core.send_influxdb import *
from functions_core.secure_connect import *


def args_setup(args):

    if args['ip_bastion']:
          bastion=str(args['ip_bastion'])
    elif args['bastion']:
          bastion=str(args['bastion'])
    else:
          bastion=None

    if args['ip_host_keys']:
          host_keys=args['ip_host_keys']
    elif args['host_keys']:
          host_keys=args['host_keys']
    else:
          host_keys=None

    if args['alias']:
        hostname = args['alias']
    else:
        hostname = str(args['ip'])
        
    args['bastion']=bastion
    args['host_keys']=host_keys
    args['hostname']=hostname

    return args  

def eternus_cs8000_fs_io(**args):

    logging.debug("Starting func_eternus_cs8000_fs_io")

    # Organize the args from ip calling specific function     
    args=args_setup(args)

    # Command line to run remotly
    cmd1="/opt/fsc/CentricStor/bin/rdNsdInfos -a > /tmp/stats_nsd.out"
    cmd2="/usr/bin/iostat -x -k 1 2| awk '!/^sd/'|awk -vN=2 '/avg-cpu/{++n} n>=N' > /tmp/stats_iostat.out"
    cmd3="awk \'NR==FNR{a[$1]=$0; next} $3 in a{print a[$3],$0}\' /tmp/stats_iostat.out /tmp/stats_nsd.out | awk '{print $18\" \"$1\" \"$2\" \"$3\" \"$4\" \"$5\" \"$6\" \"$7\" \"$8 \" \"$9\" \"$10\" \"$11\" \"$12\" \"$13\" \"$14\" \"$15\" \"$16\" \"$17}' | sort"
    
    logging.debug("Use_sudo is set to %s and ip_use_sudo %s" % (args['use_sudo'], args['ip_use_sudo']))

    if args['use_sudo'] or args['ip_use_sudo']:
            cmd1 = "sudo " + cmd1
            logging.debug("Will use cmd1 with sudo - %s" % cmd1)

    flag_test=None
    
    if os.path.isfile("tests/cafs_iostat"):
          logging.info("cafs_iostat file exists, it will be used for tests")
          flag_test=True
          cmd1 = "echo TEST"
          cmd2 = cmd1
          cmd3 = subprocess.run(['cat', './tests/cafs_iostat'], stdout=subprocess.PIPE).stdout.decode('utf-8')
          logging.debug("cmd3 for test %s" % cmd3)
          logging.warning("You are using test file for FS_IO, not really data")
          
    logging.debug("Command Line 1 - %s" % cmd1)
    logging.debug("Command Line 2 - %s" % cmd2)
    logging.debug("Command Line 3 - %s" % cmd3)

    try:
        ssh=Secure_Connect(str(args['ip']),args['bastion'],args['user'],args['host_keys'])
    except Exception as msgerror:
        logging.error(f"Failed to connect to {args['ip']} with error: {msgerror}")
        ssh.ssh_del()
        return -1
    
    logging.debug("This is my ssh session from the Class Secure_Connect %s" % ssh)
    
    NONE = ssh.ssh_run(cmd1)
    NONE = ssh.ssh_run(cmd2)

    if flag_test:
         response = cmd3
    else:
         stdout = ssh.ssh_run(cmd3)
         response = stdout.stdout

    timestamp = int(time.time())

    if len(response) == 0:
        logging.error(f"Output of iostat is empty {response}")
        return -1

    # Close ssh session
    ssh.ssh_del()
    logging.debug("Finished core function ssh with args %s" % args)
    
    logging.debug("Output of Command Line 3 - %s" % response)
    
    record = []

    logging.debug("Starting metrics processing on FS_IO")

    for line in response.splitlines():
        if not line.strip():
             continue

        if len(line.split()) == 18 and not line.startswith("\n") and not line.startswith("Device"):
            
            columns = line.split()

            record = record + [
                     {"measurement": "fs_io",
                              "tags": {"system": args['name'], "resource_type": args['resources_types'], "host": args['hostname'],
                                       "fs": str(columns[0]), "dm": str(columns[1]),"rawdev": str(columns[17])},
                              "fields": {"svctm": float(columns[15]), "r_await": float(columns[10]), "w_await": float(columns[11]), "r/s": float(columns[2]), "w/s": float(columns[3])},
                              "time": timestamp
                              }
                         ]
    
    # Send Data to InfluxDB
    logging.debug("Data to be sent to DB by FS_IO %s" % record)
    send_influxdb(str(args['repository']), str(args['repository_port']), args['repository_api_key'], args['repo_org'], args['repo_bucket'], record)
            
    logging.debug("Finished core function ssh with args %s" % args)

def eternus_cs8000_drives(**args):

    logging.debug("Starting func_eternus_cs8000_drives")

    # Organize the args from ip calling specific function     
    args=args_setup(args)

    # Command line to run remotly
    cmd1="/opt/fsc/bin/plmcmd query -D"
    
    logging.debug("Use_sudo is set to %s and ip_use_sudo %s" % (args['use_sudo'], args['ip_use_sudo']))

    if args['use_sudo'] or args['ip_use_sudo']:
            cmd1 = "sudo " + cmd1
            logging.debug("Will use cmd1 with sudo - %s" % cmd1)
    
    logging.debug("Command Line 1 - %s" % cmd1)


    flag_test=None
    
    if os.path.isfile("tests/plmcmd_query-D"):
          logging.info("plmcmd_query-D file exists, it will be used for tests")
          flag_test=True
          cmd1 = subprocess.run(['cat', './tests/plmcmd_query-D'], stdout=subprocess.PIPE).stdout.decode('utf-8')
          logging.debug("cmd1 for test %s" % cmd1)
          logging.warning("You are using test file for Drives, not really data")

    try:
        ssh=Secure_Connect(str(args['ip']),args['bastion'],args['user'],args['host_keys'])
    except Exception as msgerror:
        logging.error(f"Failed to connect to {args['ip']} with error: {msgerror}")
        ssh.ssh_del()
        return -1
    
    logging.debug("This is my ssh session from the Class Secure_Connect %s" % ssh)
    
    if flag_test:
         response = cmd1
         ssh.ssh_run("ls")
    else:
         stdout = ssh.ssh_run(cmd1)
         response = stdout.stdout

    timestamp = int(time.time())
    
    # Close ssh session
    ssh.ssh_del()        
    logging.debug("Finished core function ssh with args %s" % args)

    logging.debug("Output of Command Line 1 - %s" % response)
    
    logging.debug("Starting metrics processing on DRIVES")

    tapename = None
    count_unused = 0
    count_used = 0
    count_another_state = 0
    record=[]
    
    for line in response.splitlines():
        if not line.strip():
             continue
        
        columns = line.split()
    
        if line.startswith("Tapelibrary"):    
            if tapename != None:
          
                record = record + [{"measurement": "drives", "tags": {"system": args['name'], "resource_type": args['resources_types'], "host": args['hostname'], "tapename": tapename },
                                  "fields": {"total": int(count_used+count_unused+count_another_state), "used": int(count_used), "other": int(count_another_state)},
                                  "time": timestamp}]
    
                logging.debug("tapename %s total drives %s used %s unused %s other %s" % (tapename, count_used+count_unused+count_another_state, count_used, count_unused, count_another_state))
                count_unused = 0
                count_used = 0
                count_another_state = 0
                tapename = str(columns[1])
            else:
                tapename = str(columns[1])
        elif not columns[0].isdigit():
        #elif line.startswith("PLS") or line.startswith("pos"):
            continue
        else:
            if str(columns[2]) == "unused":
                count_unused = count_unused + 1
            elif str(columns[2]) == "occupied":
                count_used = count_used + 1
            else:
                count_another_state = count_another_state + 1
    
    record = record + [{"measurement": "drives", "tags": {"system": args['name'], "resource_type": args['resources_types'], "host": args['hostname'], "tapename": tapename },
                                  "fields": {"total": int(count_used+count_unused+count_another_state), "used": int(count_used), "other": int(count_another_state)},
                                  "time": timestamp}]

    # Send Data to InfluxDB
    logging.debug("Data to be sent to DB by drives %s" % record)
    send_influxdb(str(args['repository']), str(args['repository_port']), args['repository_api_key'], args['repo_org'], args['repo_bucket'], record)
    
    logging.debug("Finished func_eternus_cs8000_drives ")

def eternus_cs8000_medias(**args):

    logging.debug("Starting func_eternus_cs8000_medias")

    # Organize the args from ip calling specific function     
    args=args_setup(args)

    # Command line to run remotly
    cmd1="/opt/fsc/bin/plmcmd query -V"
    
    logging.debug("Use_sudo is set to %s and ip_use_sudo %s" % (args['use_sudo'], args['ip_use_sudo']))

    if args['use_sudo'] or args['ip_use_sudo']:
            cmd1 = "sudo " + cmd1
            logging.debug("Will use cmd1 with sudo - %s" % cmd1)
    
    logging.debug("Command Line 1 - %s" % cmd1)


    flag_test=None
    
    if os.path.isfile("tests/plmcmd_query-V"):
          logging.info("plmcmd_query-V file exists, it will be used for tests")
          flag_test=True
          cmd1 = subprocess.run(['cat', './tests/plmcmd_query-V'], stdout=subprocess.PIPE).stdout.decode('utf-8')
          logging.debug("cmd1 for test %s" % cmd1)
          logging.warning("You are using test file for Drives, not really data")

    try:
        ssh=Secure_Connect(str(args['ip']),args['bastion'],args['user'],args['host_keys'])
    except Exception as msgerror:
        logging.error(f"Failed to connect to {args['ip']} with error: {msgerror}")
        ssh.ssh_del()
        return -1
    
    logging.debug("This is my ssh session from the Class Secure_Connect %s" % ssh)
    
    if flag_test:
         response = cmd1
         ssh.ssh_run("ls")
    else:
         stdout = ssh.ssh_run(cmd1)
         response = stdout.stdout

    timestamp = int(time.time())
    
    # Close ssh session
    ssh.ssh_del()        
    logging.debug("Finished core function ssh with args %s" % args)

    logging.debug("Output of Command Line 1 - %s" % response)
    
    logging.debug("Starting metrics processing on MEDIAS")


    ##############################
    library = {}
    record = []
    
    for line in response.splitlines():
        if not line.strip():
             continue
        
        columns = line.split()
        
        if line.__contains__("pos"):
            continue
        else:
            # Library Libname / Count Medias / Total Cap / Total Valid / Val% / Clean / Inacessible / Fault
            # PVG_Library PVG / Total PV's / Fault / Ina / Scr / -10 / -20 / -30 / -40 / -50 / -60 / -70 / -80 / -90 / >90 / Total Cap TB / Use Cap TB
            # Scratch if fill_grade == 0 and $5 == o___
            if str(columns[2]) not in library.keys():
                if str(columns[4][0]) == 'i' and not str(columns[1]).startswith("CLN"):
                    library[str(columns[2])]=[str(columns[2]),0,0,0,0.0,0,1,0]
                elif str(columns[4][0]) == 'f' and not str(columns[1]).startswith("CLN"):
                    library[str(columns[2])]=[str(columns[2]),0,0,0,0.0,0,0,1]
                elif str(columns[1]).startswith("CLN"):
                    library[str(columns[2])]=[str(columns[2]),0,float(columns[8]),float(columns[9]),0.0,1,0,0]
                elif float(columns[8]) > 0.0 and not str(columns[1]).startswith("CLN"):
                    library[str(columns[2])]=[str(columns[2]),1,float(columns[8]),float(columns[9]),float(columns[10]),0,0,0]
                else:
                    logging.error("This line requires development analysis in metric medias -  %s" % columns)
            else:
                if str(columns[4][0]) == 'i' and not str(columns[1]).startswith("CLN"):
                    library[str(columns[2])]=[str(columns[2]),int(library[str(columns[2])][1])+0,float(library[str(columns[2])][2]),float(library[str(columns[2])][3]),float(library[str(columns[2])][4]),int(library[str(columns[2])][5])+0,int(library[str(columns[2])][6])+1,int(library[str(columns[2])][7])+0]
                elif str(columns[4][0]) == 'f' and not str(columns[1]).startswith("CLN"):
                    library[str(columns[2])]=[str(columns[2]),int(library[str(columns[2])][1])+0,float(library[str(columns[2])][2]),float(library[str(columns[2])][3]),float(library[str(columns[2])][4]),int(library[str(columns[2])][5])+0,int(library[str(columns[2])][6])+0,int(library[str(columns[2])][7])+1]
                elif str(columns[1]).startswith("CLN"):
                    library[str(columns[2])]=[str(columns[2]),int(library[str(columns[2])][1])+0,float(library[str(columns[2])][2]),float(library[str(columns[2])][3]),float(library[str(columns[2])][4]),int(library[str(columns[2])][5])+1,int(library[str(columns[2])][6])+0,int(library[str(columns[2])][7])+0]
                elif float(columns[8]) > 0 and not str(columns[1]).startswith("CLN"):
                    library[str(columns[2])]=[str(columns[2]),int(library[str(columns[2])][1])+1,float(library[str(columns[2])][2])+float(columns[8]),float(library[str(columns[2])][3])+float(columns[9]),float(library[str(columns[2])][4])+float(columns[10]),int(library[str(columns[2])][5])+0,int(library[str(columns[2])][6])+0,int(library[str(columns[2])][7])+0]
                else:
                    logging.error("This line requires development analysis in metric medias -  %s" % columns)

    for line in library.values():
        if line[4] != 0 and line[1] != 0:
            line[4]=line[4]/line[1]

        record = record + [{"measurement": "medias", "tags": {"system": args['name'], "resource_type": args['resources_types'], "host": args['hostname'], "tapename": line[0] },
                                  "fields": {"Total Medias": line[1], "Total Cap GiB": line[2], "Total Val GiB": line[3], "Val %": line[4], "Total Clean Medias": line[5], "Total Ina": line[6], "Total Fault": line[7]},
                                  "time": timestamp}]
    ########################

    # Send Data to InfluxDB
    logging.debug("Data to be sent to DB by medias %s" % record)
    send_influxdb(str(args['repository']), str(args['repository_port']), args['repository_api_key'], args['repo_org'], args['repo_bucket'], record)
    
    logging.debug("Finished func_eternus_cs8000_medias")

def eternus_cs8000_pvgprofile(**args):

    logging.debug("Starting func_eternus_cs8000_pvgprofile")

    # Organize the args from ip calling specific function     
    args=args_setup(args)

    # Command line to run remotly
    cmd1="/opt/fsc/bin/plmcmd query -V | grep -v CLN | grep -v \'PVG\'"
    
    logging.debug("Use_sudo is set to %s and ip_use_sudo %s" % (args['use_sudo'], args['ip_use_sudo']))

    if args['use_sudo'] or args['ip_use_sudo']:
            cmd1 = "sudo " + cmd1
            logging.debug("Will use cmd1 with sudo - %s" % cmd1)
    
    logging.debug("Command Line 1 - %s" % cmd1)

    flag_test=None
    
    if os.path.isfile("./tests/plmcmd_pvgprofile"):
          logging.info("plmcmd_pvgprofile file exists, it will be used for tests")
          flag_test=True
          cmd="cat ./tests/plmcmd_pvgprofile | grep -v \'CLN\' | grep -v \'PVG\'"
          cmd1 = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
          logging.debug("cmd1 for test %s" % cmd1)
          logging.warning("You are using test file for PVG Profile, not really data")

    try:
        ssh=Secure_Connect(str(args['ip']),args['bastion'],args['user'],args['host_keys'])
    except Exception as msgerror:
        logging.error(f"Failed to connect to {args['ip']} with error: {msgerror}")
        ssh.ssh_del()
        return -1
    
    logging.debug("This is my ssh session from the Class Secure_Connect %s" % ssh)
    
    if flag_test:
         response = cmd1
         ssh.ssh_run("ls")
    else:
         stdout = ssh.ssh_run(cmd1)
         response = stdout.stdout

    timestamp = int(time.time())

    # Close ssh session
    ssh.ssh_del()
    logging.debug("Finished core function ssh with args %s" % args)

    logging.debug("Output of Command Line 1 - %s" % response)
    
    logging.debug("Starting metrics processing on PVGProfile")


    ##############################
    library = {}
    record = []

    for line in response.splitlines():
        if not line.strip():
             continue
                
        columns = line.split()
        if line.__contains__("PVG"):
            continue
        else:
            if str(columns[3]) not in library.keys():
                if str(columns[4][0]) == 'f':
                    library[str(columns[3])]=[str(columns[3]),1,1,0,0,0,0,0,0,0,0,0,0,0,0,0.0,0.0]
                elif str(columns[4][0]) == 'i':
                    library[str(columns[3])]=[str(columns[3]),1,0,1,0,0,0,0,0,0,0,0,0,0,0,0.0,0.0]
                elif float(columns[10]) == 0 and str(columns[4][0]) == 'o':
                    library[str(columns[3])]=[str(columns[3]),1,0,0,1,0,0,0,0,0,0,0,0,0,0,float(columns[8]),float(columns[9])]
                elif float(columns[10]) >= 0:
                    if float(columns[10]) < 10:
                        library[str(columns[3])]=[str(columns[3]),1,0,0,0,1,0,0,0,0,0,0,0,0,0,float(columns[8]),float(columns[9])]
                    elif float(columns[10]) >= 10 and float(columns[10]) < 20:
                        library[str(columns[3])]=[str(columns[3]),1,0,0,0,0,1,0,0,0,0,0,0,0,0,float(columns[8]),float(columns[9])]
                    elif float(columns[10]) >= 20 and float(columns[10]) < 30:
                        library[str(columns[3])]=[str(columns[3]),1,0,0,0,0,0,1,0,0,0,0,0,0,0,float(columns[8]),float(columns[9])]
                    elif float(columns[10]) >= 30 and float(columns[10]) < 40:
                        library[str(columns[3])]=[str(columns[3]),1,0,0,0,0,0,0,1,0,0,0,0,0,0,float(columns[8]),float(columns[9])]
                    elif float(columns[10]) >= 40 and float(columns[10]) < 50:
                        library[str(columns[3])]=[str(columns[3]),1,0,0,0,0,0,0,0,1,0,0,0,0,0,float(columns[8]),float(columns[9])]
                    elif float(columns[10]) >= 50 and float(columns[10]) < 60:
                        library[str(columns[3])]=[str(columns[3]),1,0,0,0,0,0,0,0,0,1,0,0,0,0,float(columns[8]),float(columns[9])]
                    elif float(columns[10]) >= 60 and float(columns[10]) < 70:
                        library[str(columns[3])]=[str(columns[3]),1,0,0,0,0,0,0,0,0,0,1,0,0,0,float(columns[8]),float(columns[9])]
                    elif float(columns[10]) >= 70 and float(columns[10]) < 80:
                        library[str(columns[3])]=[str(columns[3]),1,0,0,0,0,0,0,0,0,0,0,1,0,0,float(columns[8]),float(columns[9])]
                    elif float(columns[10]) >= 80 and float(columns[10]) < 90:
                        library[str(columns[3])]=[str(columns[3]),1,0,0,0,0,0,0,0,0,0,0,0,1,0,float(columns[8]),float(columns[9])]
                    elif float(columns[10]) >= 90:
                        library[str(columns[3])]=[str(columns[3]),1,0,0,0,0,0,0,0,0,0,0,0,0,1,float(columns[8]),float(columns[9])]
                    else:
                        logging.error("This line requires development analysis in metric PVGPROFILE -  %s" % columns)
                else:
                    logging.error("This line requires development analysis  in metric PVGPROFILE -  %s" % columns)
            # PVG_Library PVG / Total PV's / Fault / Ina / Scr / -10 / -20 / -30 / -40 / -50 / -60 / -70 / -80 / -90 / >90 / Total Cap TB / Use Cap TB
            else:
                #                            tapename 0       Total PVG 1                           Fault 2                              Ina 3                            Scr 4                                -10 5                                -20 6                               -30 7                                -40 8                            -50 9                                -60 10                                -70 11                                -80 12                                -90 13                                +90 14                                Total Cap 15        Used Cap 16
                #library[str(columns[3])]=[str(columns[3]),int(library[str(columns[3][1])])+0,int(library[str(columns[3])][2])+0,int(library[str(columns[3])][3])+0,int(library[str(columns[3])][4])+0,int(library[str(columns[3])][5])+0,int(library[str(columns[3])][6])+0,int(library[str(columns[3])][7])+0,int(library[str(columns[3])][8])+0,int(library[str(columns[3])][9])+0,int(library[str(columns[3])][10])+0,int(library[str(columns[3])][11])+0,int(library[str(columns[3])][12])+0,int(library[str(columns[3])][13])+0,int(library[str(columns[3])][14])+0,float(library[str(columns[3])][15])+0,float(library[str(columns[3])][16])+0]
                if str(columns[4][0]) == 'f':
                    library[str(columns[3])]=[str(columns[3]),int(library[str(columns[3])][1])+1,int(library[str(columns[3])][2])+1,int(library[str(columns[3])][3])+0,int(library[str(columns[3])][4])+0,int(library[str(columns[3])][5])+0,int(library[str(columns[3])][6])+0,int(library[str(columns[3])][7])+0,int(library[str(columns[3])][8])+0,int(library[str(columns[3])][9])+0,int(library[str(columns[3])][10])+0,int(library[str(columns[3])][11])+0,int(library[str(columns[3])][12])+0,int(library[str(columns[3])][13])+0,int(library[str(columns[3])][14])+0,float(library[str(columns[3])][15])+0,float(library[str(columns[3])][16])+0]
                elif str(columns[4][0]) == 'i':
                    library[str(columns[3])]=[str(columns[3]),int(library[str(columns[3])][1])+1,int(library[str(columns[3])][2])+0,int(library[str(columns[3])][3])+1,int(library[str(columns[3])][4])+0,int(library[str(columns[3])][5])+0,int(library[str(columns[3])][6])+0,int(library[str(columns[3])][7])+0,int(library[str(columns[3])][8])+0,int(library[str(columns[3])][9])+0,int(library[str(columns[3])][10])+0,int(library[str(columns[3])][11])+0,int(library[str(columns[3])][12])+0,int(library[str(columns[3])][13])+0,int(library[str(columns[3])][14])+0,float(library[str(columns[3])][15])+0,float(library[str(columns[3])][16])+0]
                elif float(columns[10]) == 0 and str(columns[4][0]) == 'o':
                    library[str(columns[3])]=[str(columns[3]),int(library[str(columns[3])][1])+1,int(library[str(columns[3])][2])+0,int(library[str(columns[3])][3])+0,int(library[str(columns[3])][4])+1,int(library[str(columns[3])][5])+0,int(library[str(columns[3])][6])+0,int(library[str(columns[3])][7])+0,int(library[str(columns[3])][8])+0,int(library[str(columns[3])][9])+0,int(library[str(columns[3])][10])+0,int(library[str(columns[3])][11])+0,int(library[str(columns[3])][12])+0,int(library[str(columns[3])][13])+0,int(library[str(columns[3])][14])+0,float(library[str(columns[3])][15])+float(columns[8]),float(library[str(columns[3])][16])+float(columns[9])]
                elif float(columns[10]) >= 0:
                    if float(columns[10]) < 10:
                        library[str(columns[3])]=[str(columns[3]),int(library[str(columns[3])][1])+1,int(library[str(columns[3])][2])+0,int(library[str(columns[3])][3])+0,int(library[str(columns[3])][4])+0,int(library[str(columns[3])][5])+1,int(library[str(columns[3])][6])+0,int(library[str(columns[3])][7])+0,int(library[str(columns[3])][8])+0,int(library[str(columns[3])][9])+0,int(library[str(columns[3])][10])+0,int(library[str(columns[3])][11])+0,int(library[str(columns[3])][12])+0,int(library[str(columns[3])][13])+0,int(library[str(columns[3])][14])+0,float(library[str(columns[3])][15])+float(columns[8]),float(library[str(columns[3])][16])+float(columns[9])]
                    elif float(columns[10]) >= 10 and float(columns[10]) < 20:
                        library[str(columns[3])]=[str(columns[3]),int(library[str(columns[3])][1])+1,int(library[str(columns[3])][2])+0,int(library[str(columns[3])][3])+0,int(library[str(columns[3])][4])+0,int(library[str(columns[3])][5])+0,int(library[str(columns[3])][6])+1,int(library[str(columns[3])][7])+0,int(library[str(columns[3])][8])+0,int(library[str(columns[3])][9])+0,int(library[str(columns[3])][10])+0,int(library[str(columns[3])][11])+0,int(library[str(columns[3])][12])+0,int(library[str(columns[3])][13])+0,int(library[str(columns[3])][14])+0,float(library[str(columns[3])][15])+float(columns[8]),float(library[str(columns[3])][16])+float(columns[9])]
                    elif float(columns[10]) >= 20 and float(columns[10]) < 30:
                        library[str(columns[3])]=[str(columns[3]),int(library[str(columns[3])][1])+1,int(library[str(columns[3])][2])+0,int(library[str(columns[3])][3])+0,int(library[str(columns[3])][4])+0,int(library[str(columns[3])][5])+0,int(library[str(columns[3])][6])+0,int(library[str(columns[3])][7])+1,int(library[str(columns[3])][8])+0,int(library[str(columns[3])][9])+0,int(library[str(columns[3])][10])+0,int(library[str(columns[3])][11])+0,int(library[str(columns[3])][12])+0,int(library[str(columns[3])][13])+0,int(library[str(columns[3])][14])+0,float(library[str(columns[3])][15])+float(columns[8]),float(library[str(columns[3])][16])+float(columns[9])]
                    elif float(columns[10]) >= 30 and float(columns[10]) < 40:
                        library[str(columns[3])]=[str(columns[3]),int(library[str(columns[3])][1])+1,int(library[str(columns[3])][2])+0,int(library[str(columns[3])][3])+0,int(library[str(columns[3])][4])+0,int(library[str(columns[3])][5])+0,int(library[str(columns[3])][6])+0,int(library[str(columns[3])][7])+0,int(library[str(columns[3])][8])+1,int(library[str(columns[3])][9])+0,int(library[str(columns[3])][10])+0,int(library[str(columns[3])][11])+0,int(library[str(columns[3])][12])+0,int(library[str(columns[3])][13])+0,int(library[str(columns[3])][14])+0,float(library[str(columns[3])][15])+float(columns[8]),float(library[str(columns[3])][16])+float(columns[9])]
                    elif float(columns[10]) >= 40 and float(columns[10]) < 50:
                        library[str(columns[3])]=[str(columns[3]),int(library[str(columns[3])][1])+1,int(library[str(columns[3])][2])+0,int(library[str(columns[3])][3])+0,int(library[str(columns[3])][4])+0,int(library[str(columns[3])][5])+0,int(library[str(columns[3])][6])+0,int(library[str(columns[3])][7])+0,int(library[str(columns[3])][8])+0,int(library[str(columns[3])][9])+1,int(library[str(columns[3])][10])+0,int(library[str(columns[3])][11])+0,int(library[str(columns[3])][12])+0,int(library[str(columns[3])][13])+0,int(library[str(columns[3])][14])+0,float(library[str(columns[3])][15])+float(columns[8]),float(library[str(columns[3])][16])+float(columns[9])]
                    elif float(columns[10]) >= 50 and float(columns[10]) < 60:
                        library[str(columns[3])]=[str(columns[3]),int(library[str(columns[3])][1])+1,int(library[str(columns[3])][2])+0,int(library[str(columns[3])][3])+0,int(library[str(columns[3])][4])+0,int(library[str(columns[3])][5])+0,int(library[str(columns[3])][6])+0,int(library[str(columns[3])][7])+0,int(library[str(columns[3])][8])+0,int(library[str(columns[3])][9])+0,int(library[str(columns[3])][10])+1,int(library[str(columns[3])][11])+0,int(library[str(columns[3])][12])+0,int(library[str(columns[3])][13])+0,int(library[str(columns[3])][14])+0,float(library[str(columns[3])][15])+float(columns[8]),float(library[str(columns[3])][16])+float(columns[9])]
                    elif float(columns[10]) >= 60 and float(columns[10]) < 70:
                        library[str(columns[3])]=[str(columns[3]),int(library[str(columns[3])][1])+1,int(library[str(columns[3])][2])+0,int(library[str(columns[3])][3])+0,int(library[str(columns[3])][4])+0,int(library[str(columns[3])][5])+0,int(library[str(columns[3])][6])+0,int(library[str(columns[3])][7])+0,int(library[str(columns[3])][8])+0,int(library[str(columns[3])][9])+0,int(library[str(columns[3])][10])+0,int(library[str(columns[3])][11])+1,int(library[str(columns[3])][12])+0,int(library[str(columns[3])][13])+0,int(library[str(columns[3])][14])+0,float(library[str(columns[3])][15])+float(columns[8]),float(library[str(columns[3])][16])+float(columns[9])]
                    elif float(columns[10]) >= 70 and float(columns[10]) < 80:
                        library[str(columns[3])]=[str(columns[3]),int(library[str(columns[3])][1])+1,int(library[str(columns[3])][2])+0,int(library[str(columns[3])][3])+0,int(library[str(columns[3])][4])+0,int(library[str(columns[3])][5])+0,int(library[str(columns[3])][6])+0,int(library[str(columns[3])][7])+0,int(library[str(columns[3])][8])+0,int(library[str(columns[3])][9])+0,int(library[str(columns[3])][10])+0,int(library[str(columns[3])][11])+0,int(library[str(columns[3])][12])+1,int(library[str(columns[3])][13])+0,int(library[str(columns[3])][14])+0,float(library[str(columns[3])][15])+float(columns[8]),float(library[str(columns[3])][16])+float(columns[9])]
                    elif float(columns[10]) >= 80 and float(columns[10]) < 90:
                        library[str(columns[3])]=[str(columns[3]),int(library[str(columns[3])][1])+1,int(library[str(columns[3])][2])+0,int(library[str(columns[3])][3])+0,int(library[str(columns[3])][4])+0,int(library[str(columns[3])][5])+0,int(library[str(columns[3])][6])+0,int(library[str(columns[3])][7])+0,int(library[str(columns[3])][8])+0,int(library[str(columns[3])][9])+0,int(library[str(columns[3])][10])+0,int(library[str(columns[3])][11])+0,int(library[str(columns[3])][12])+0,int(library[str(columns[3])][13])+1,int(library[str(columns[3])][14])+0,float(library[str(columns[3])][15])+float(columns[8]),float(library[str(columns[3])][16])+float(columns[9])]
                    elif float(columns[10]) >= 90:
                        library[str(columns[3])]=[str(columns[3]),int(library[str(columns[3])][1])+1,int(library[str(columns[3])][2])+0,int(library[str(columns[3])][3])+0,int(library[str(columns[3])][4])+0,int(library[str(columns[3])][5])+0,int(library[str(columns[3])][6])+0,int(library[str(columns[3])][7])+0,int(library[str(columns[3])][8])+0,int(library[str(columns[3])][9])+0,int(library[str(columns[3])][10])+0,int(library[str(columns[3])][11])+0,int(library[str(columns[3])][12])+0,int(library[str(columns[3])][13])+0,int(library[str(columns[3])][14])+1,float(library[str(columns[3])][15])+float(columns[8]),float(library[str(columns[3])][16])+float(columns[9])]
                    else:
                        logging.error("This line requires development analysis in metric PVGPROFILE -  %s" % columns)
                else:
                    logging.error("This line requires development analysis in metric PVGPROFILE -  %s" % columns)

    for line in library.values():
        # PVG_Library PVG / Total PV's / Fault / Ina / Scr / -10 / -20 / -30 / -40 / -50 / -60 / -70 / -80 / -90 / >90 / Total Cap TB / Use Cap TB
        record = record + [{"measurement": "pvgprofile", "tags": {"system": args['name'], "resource_type": args['resources_types'], "host": args['hostname'], "pvgname": line[0] },
                                  "fields": {"Total Medias": line[1], "Fault": line[2], "Ina": line[3], "Scr": line[4], "-10": line[5], "-20": line[6], "-30": line[7], "-40": line[8], "-50": line[9], "-60": line[10], "-70": line[11], "-80": line[12], "-90": line[13], ">90": line[14], "Total Cap (GiB)": line[15], "Total Used (GiB)": line[16]},
                                  "time": timestamp}]
    ########################

    # Send Data to InfluxDB
    logging.debug("Data to be sent to DB by pvgprofile %s" % record)
    send_influxdb(str(args['repository']), str(args['repository_port']), args['repository_api_key'], args['repo_org'], args['repo_bucket'], record)
    
    logging.debug("Finished func_eternus_cs8000_pvgprofile")

def eternus_cs8000_fc(**args):

    logging.debug("Starting func_eternus_cs8000_fc")
    
    # Organize the args from ip calling specific function     
    args=args_setup(args)

    # Open ssh session
    try:
        ssh=Secure_Connect(str(args['ip']),args['bastion'],args['user'],args['host_keys'])
    except Exception as msgerror:
        logging.error(f"Failed to connect to {args['ip']} with error: {msgerror}")
        ssh.ssh_del()
        return -1
    
    logging.debug("This is my ssh session from the Class Secure_Connect %s" % ssh)
    

    ########## WILL EXECUTE MAIN SSH COMMANDS ###########################        
    try:
        cmd1="for hosthba in `ls /sys/class/fc_host`;do WWN=`cat /sys/class/fc_host/$hosthba/port_name | sed 's/^0x//' | sed 's/../&:/g;s/:$//'`; echo $hosthba $WWN; done"
        logging.debug("Command Line 1 - %s" % cmd1)
        stdoutcmd1 = ssh.ssh_run(cmd1)
        logging.debug("Output of Command Line 1:\n%s" % stdoutcmd1.stdout)
        
        cmd2="lsscsi | awk '{ print $1, $2 }' | grep disk"
        logging.debug("Command Line 2 - %s" % cmd2)
        stdoutcmd2 = ssh.ssh_run(cmd2)
        logging.debug("Output of Command Line 2:\n%s" % stdoutcmd2.stdout)
        
        cmd3="lsscsi | awk '{ print $1, $2 }' | grep tape"
        logging.debug("Command Line 3 - %s" % cmd3)
        stdoutcmd3 = ssh.ssh_run(cmd3)
        logging.debug("Output of Command Line 3:\n%s" % stdoutcmd3.stdout)
        
        cmd4="ls /sys/kernel/config/target/qla2xxx | grep :"
        logging.debug("Command Line 4 - %s" % cmd4)    
        stdoutcmd4 = ssh.ssh_run(cmd4)
        logging.debug("Output of Command Line 4:\n%s" % stdoutcmd4.stdout)
        
        cmd5="cat /etc/os-release | grep VERSION_ID"
        logging.debug("Command Line 5 - %s" % cmd5)
        stdoutcmd5 = ssh.ssh_run(cmd5)
        logging.debug("Output of Command Line 5:\n%s" % stdoutcmd5.stdout)
        
        #if stdoutcmd1.stderr or stdoutcmd2.stderr or stdoutcmd3.stderr or stdoutcmd4.stderr or stdoutcmd5.stderr:
        #    logging.error("Got error from one of the commands line:\n%s %s %s %s %s" % (stdoutcmd1.error, stdoutcmd2.error, stdoutcmd3.error, stdoutcmd4.error, stdoutcmd5.error))
        #    return -1
    except Exception as msgerror:
        logging.error("Failed the cmd execution in %s with error %s" % (args['ip'], msgerror))
        ssh.ssh_del()
        return -1
    ########## END EXECUTE MAIN SSH COMMANDS ###########################        
        
    ########## WILL PROCESS THE COMMANDS OUTPUT ###########################
        
    os_ver = re.search(r'\d+(\.\d+)?', stdoutcmd5.stdout)
    if os_ver:
         os_ver = float(os_ver.group())
    else:
         logging.error("Failed to get the OS version, consider the output %s"% stdoutcmd5.stdout)
         return -1
    hostctlint = list(set(f'host{match}' for line in stdoutcmd2.stdout.split('\n') for match in re.findall(r'\[(\d+):', line)))
    hostctlbe = list(set(f'host{match}' for line in stdoutcmd3.stdout.split('\n') for match in re.findall(r'\[(\d+):', line)))
    hosttgt = stdoutcmd4.stdout
    logging.debug(f"Internal List Host Controller {hostctlint}")
    logging.debug(f"BackEnd List Host Controller {hostctlbe}")
    logging.debug(f"Target WWN's {hosttgt}")

    record=[]
    ########## WILL PROCESS INTERNAL HBA's ################################
    for line in hostctlint:
        if line in stdoutcmd1.stdout:
            if not line.strip():
                continue
            logging.debug(f"Will process internal HBA {line}")
            if os_ver >= 15:
                logging.debug(f"OS Version is >= 15 it's {os_ver}")
                try:
                    tx_mbytes = ssh.ssh_run(f"cat /sys/class/fc_host/{line}/statistics/fcp_output_megabytes")
                    rx_mbytes = ssh.ssh_run(f"cat /sys/class/fc_host/{line}/statistics/fcp_input_megabytes")
                    logging.debug(f"Controller is {line} and the tx output is {tx_mbytes.stdout} and the rx {rx_mbytes.stdout}")
                    tx_mbytes = int(tx_mbytes.stdout, 16)
                    rx_mbytes = int(rx_mbytes.stdout, 16)
                except Exception as msgerror:
                    logging.error("Failed the cmd execution for mbytes calculation in %s with error %s" % (args['ip'], msgerror))
                    ssh.ssh_del()
                    return -1
            else:
                logging.debug(f"OS Version is < 15 it's {os_ver}")
                try:
                    tx_mbytes = ssh.ssh_run(f"cat /sys/class/fc_host/{line}/statistics/tx_words")
                    rx_mbytes = ssh.ssh_run(f"cat /sys/class/fc_host/{line}/statistics/rx_words")
                    logging.debug(f"Controller is {line} and the tx output is {tx_mbytes.stdout} and the rx {rx_mbytes.stdout}")
                    tx_mbytes = int(int(tx_mbytes.stdout, 16)*4 / (1024*1024))
                    rx_mbytes = int(int(rx_mbytes.stdout, 16)*4 / (1024*1024))
                except Exception as msgerror:
                    logging.error("Failed the cmd execution for mbytes calculation in %s with error %s" % (args['ip'], msgerror))
                    ssh.ssh_del()
                    return -1
            
            timestamp = int(time.time())    
            record = record + [
            {"measurement": "fc",
            "tags": {"system": args['name'], "resource_type": args['resources_types'], "host": args['hostname'],
            "hba": line+"-int"},
            "fields": {"rx_bytes": rx_mbytes, "tx_bytes": tx_mbytes},
            "time": timestamp
            }]
    ########## WILL PROCESS BACKEND HBA's ################################
    for line in hostctlbe:
        if line in stdoutcmd1.stdout:            
            if not line.strip():
                continue
            logging.debug(f"Will process backend HBA {line}")
            if os_ver >= 15:
                logging.debug(f"OS Version is >= 15 it's {os_ver}")
                try:
                    tx_mbytes = ssh.ssh_run(f"cat /sys/class/fc_host/{line}/statistics/fcp_output_megabytes")
                    rx_mbytes = ssh.ssh_run(f"cat /sys/class/fc_host/{line}/statistics/fcp_input_megabytes")
                    logging.debug(f"Controller is {line} and the tx output is {tx_mbytes.stdout} and the rx {rx_mbytes.stdout}")
                    tx_mbytes = int(tx_mbytes.stdout, 16)
                    rx_mbytes = int(rx_mbytes.stdout, 16)
                except Exception as msgerror:
                    logging.error("Failed the cmd execution for mbytes calculation in %s with error %s" % (args['ip'], msgerror))
                    ssh.ssh_del()
                    return -1
            else:
                try:
                    logging.debug(f"OS Version is < 15 it's {os_ver}")
                    tx_mbytes = ssh.ssh_run(f"cat /sys/class/fc_host/{line}/statistics/tx_words")
                    rx_mbytes = ssh.ssh_run(f"cat /sys/class/fc_host/{line}/statistics/rx_words")
                    logging.debug(f"Controller is {line} and the tx output is {tx_mbytes.stdout} and the rx {rx_mbytes.stdout}")
                    tx_mbytes = int(int(tx_mbytes.stdout, 16)*4 / (1024*1024))
                    rx_mbytes = int(int(rx_mbytes.stdout, 16)*4 / (1024*1024))
                except Exception as msgerror:
                    logging.error("Failed the cmd execution for mbytes calculation in %s with error %s" % (args['ip'], msgerror))
                    ssh.ssh_del()
                    return -1
            timestamp = int(time.time())                    
            record = record + [
            {"measurement": "fc",
            "tags": {"system": args['name'], "resource_type": args['resources_types'], "host": args['hostname'],
            "hba": line+"-be"},
            "fields": {"rx_bytes": rx_mbytes, "tx_bytes": tx_mbytes},
            "time": timestamp
            }]
                 
    ########## WILL PROCESS TARGET HBA's #################################
    if hosttgt:
        for line in hosttgt.splitlines():
            if not line.strip():
                continue
            if line in stdoutcmd1.stdout:
                hostctltgt = next((host.split()[0] for host in stdoutcmd1.stdout.split('\n') if line in host), None)
                #hostctltgt = next((hostctl for hostctl in stdoutcmd1.stdout.split() if hostctl == line), None)
                logging.debug(f"Target Controller with WWN {line} is HBA {hostctltgt}")
                try:
                    tx_mbytes = ssh.ssh_run(f"cat /sys/kernel/config/target/qla2xxx/{line}/tpgt_1/lun/lun_*/statistics/scsi_tgt_port/read_mbytes|awk '{{ sum += $1 }} END {{ print sum }}'")
                    rx_mbytes = ssh.ssh_run(f"cat /sys/kernel/config/target/qla2xxx/{line}/tpgt_1/lun/lun_*/statistics/scsi_tgt_port/write_mbytes|awk '{{ sum += $1 }} END {{ print sum }}'")
                    logging.debug(f"Controller is {line} and the tx output is {tx_mbytes.stdout} and the rx {rx_mbytes.stdout}")
                except Exception as msgerror:
                    logging.error("Failed the cmd execution for mbytes calculation in %s with error %s" % (args['ip'], msgerror))
                    ssh.ssh_del()
                    return -1
            else:
                logging.error("Can't find the wwn from the target in the list of host controllers:\n%s" % line)
                return -1
            timestamp = int(time.time())                    
            record = record + [
            {"measurement": "fc",
            "tags": {"system": args['name'], "resource_type": args['resources_types'], "host": args['hostname'],
            "hba": hostctltgt+"-tgt"},
            "fields": {"rx_bytes": int(rx_mbytes.stdout), "tx_bytes": int(tx_mbytes.stdout)},
            "time": timestamp
            }]

########## END PROCESS THE COMMANDS OUTPUT ############################

    # Close ssh session
    ssh.ssh_del()
    logging.debug("Finished core function ssh with args:\n%s" % args)

    # Send Data to InfluxDB
    if record:
        logging.debug("Data to be sent to DB by fc:\n%s" % record)
        send_influxdb(str(args['repository']), str(args['repository_port']), args['repository_api_key'], args['repo_org'], args['repo_bucket'], record)
    else:
         logging.warning(f"There is no data to be sent to influxdb, are you in the correct system with the correct metrics?")
    logging.debug("Finished func_eternus_cs8000_fc")



def eternus_cs8000_vtldirtycache(**args):

    logging.debug("Starting func_eternus_cs8000_vtldirtycache")
    
    # Organize the args from ip calling specific function     
    args=args_setup(args)

    # Open ssh session
    try:
        ssh=Secure_Connect(str(args['ip']),args['bastion'],args['user'],args['host_keys'])
    except Exception as msgerror:
        logging.error(f"Failed to connect to {args['ip']} with error: {msgerror}")
        ssh.ssh_del()
        return -1
    
    logging.debug("This is my ssh session from the Class Secure_Connect %s" % ssh)
    

    ########## WILL EXECUTE MAIN SSH COMMANDS ###########################        
    try:
        cmd1="vlmcmd cstat"
        logging.debug(f"Command Line 1 - {cmd1}")
        stdout = ssh.ssh_run(cmd1)
        response = stdout.stdout
        logging.debug(f"Output of Command Line 1:\n {response}")
    except Exception as msgerror:
        logging.error(f"Failed the cmd execution in {args['ip']} with error {msgerror}")
        ssh.ssh_del()
        return -1

    timestamp = int(time.time())

    # Assuming 'output' contains the output of the command "vlmcmd cstat"
    #output = """
    #/cache/100: (exclusive) retention: 31.32% violated: 11 Volume(s)
    #used: 1.82% dirty: 69.56% retained: 0.04% clean: 22.50% free: 6.08%
    #
    #/cache/101: (exclusive) retention: 0.00%
    #used: 0.18% dirty: 38.81% retained: 0.00% clean: 54.95% free: 6.06%
    #
    #Virtual Volumes: 96297
    #
    #Home: 96187 Volume(s)
    #Restoring: 1 Volume(s)
    #Mounted: 109 Volume(s)
    #"""

    # Split the output string by lines
    lines = response.strip().split('\n')

    # Create a DataFrame from the lines
    df = pd.DataFrame({'Line': lines})

    # Filter rows containing '/cache' in the Line column
    cache_df = df[df['Line'].str.contains('/cache')].copy()

    # Reset the index of cache_df
    cache_df.reset_index(drop=True, inplace=True)

    # Extract filesystem names
    cache_df.loc[:, 'Filesystem'] = cache_df['Line'].str.split(':').str[0].str.strip()

    # Filter lines containing "dirty" values
    dirty_lines = df[df['Line'].str.contains('dirty')]['Line']

    # Extract "dirty" values from the filtered lines
    dirty_values = dirty_lines.str.extract(r'dirty:\s*([\d.]+)%').astype(float)

    # Reset the index of dirty_values DataFrame
    dirty_values.reset_index(drop=True, inplace=True)

    # Assign "dirty" values to the Dirty column
    cache_df.loc[:, 'Dirty'] = dirty_values

    # Drop unnecessary columns
    cache_df.drop(columns=['Line'], inplace=True)

    #print(cache_df.to_string(header=False, index=False))
    record = []
    for index, row in cache_df.iterrows():
        print(row['Filesystem'], row['Dirty'])
        record = record + [
            {"measurement": "fc",
            "tags": {"system": args['name'], "resource_type": args['resources_types'], "host": args['hostname'],
            "vtldirtycachefs": row['Filesystem']},
            "fields": {"dirty%": float(row['Dirty'])},
            "time": timestamp
            }]
        #Send
    
    # Send Data to InfluxDB
    if record:
        logging.debug("Data to be sent to DB by vtldirtycache:\n%s" % record)
        send_influxdb(str(args['repository']), str(args['repository_port']), args['repository_api_key'], args['repo_org'], args['repo_bucket'], record)
    else:
         logging.warning(f"There is no data to be sent to influxdb, are you in the correct system with the correct metrics?")
    logging.debug("Finished func_eternus_cs8000_vtldirtycache")