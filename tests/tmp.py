import os, subprocess

if os.path.isfile("plmcmd_query-V"):
    cmd1 = subprocess.run(['cat', 'plmcmd_query-V'], stdout=subprocess.PIPE).stdout.decode('utf-8')


##############################
    library = {}

    for line in cmd1.splitlines():
        columns = line.split()
        if line.startswith("pos"):
            continue
        else:
            # Lib / Count Medias / Total Cap / Total Valid / Val% / Clean / Inacessible / Fault    
            if str(columns[2]) not in library.keys():
                if str(columns[4][0]) == 'i' and not str(columns[1]).startswith("CLN"):
                    library[str(columns[2])]=[str(columns[2]),0,0,0,0,0,1,0]
                elif str(columns[4][0]) == 'f' and not str(columns[1]).startswith("CLN"):
                    library[str(columns[2])]=[str(columns[2]),0,0,0,0,0,0,1]
                elif str(columns[1]).startswith("CLN"):
                    library[str(columns[2])]=[str(columns[2]),0,float(columns[8]),float(columns[9]),0,1,0,0]
                elif float(columns[8]) > 0 and not str(columns[1]).startswith("CLN"):
                    library[str(columns[2])]=[str(columns[2]),1,float(columns[8]),float(columns[9]),int(columns[10]),0,0,0]
                else:
                    print("This line has not application %s" % columns)
            else:
                if str(columns[4][0]) == 'i' and not str(columns[1]).startswith("CLN"):
                    print("Ina")
                    library[str(columns[2])]=[str(columns[2]),int(library[str(columns[2])][1])+0,float(library[str(columns[2])][2]),float(library[str(columns[2])][3]),float(library[str(columns[2])][4]),int(library[str(columns[2])][5])+0,int(library[str(columns[2])][6])+1,int(library[str(columns[2])][7])+0]
                elif str(columns[4][0]) == 'f' and not str(columns[1]).startswith("CLN"):
                    library[str(columns[2])]=[str(columns[2]),int(library[str(columns[2])][1])+0,float(library[str(columns[2])][2]),float(library[str(columns[2])][3]),float(library[str(columns[2])][4]),int(library[str(columns[2])][5])+0,int(library[str(columns[2])][6])+0,int(library[str(columns[2])][7])+1]
                elif str(columns[1]).startswith("CLN"):
                    library[str(columns[2])]=[str(columns[2]),int(library[str(columns[2])][1])+0,int(library[str(columns[2])][2]),int(library[str(columns[2])][3]),int(library[str(columns[2])][4]),int(library[str(columns[2])][5])+1,int(library[str(columns[2])][6])+0,int(library[str(columns[2])][7])+0]
                elif float(columns[8]) > 0 and not str(columns[1]).startswith("CLN"):
                    library[str(columns[2])]=[str(columns[2]),int(library[str(columns[2])][1])+1,float(library[str(columns[2])][2])+float(columns[8]),float(library[str(columns[2])][3])+float(columns[9]),int(library[str(columns[2])][4])+int(columns[10]),int(library[str(columns[2])][5])+0,int(library[str(columns[2])][6])+0,int(library[str(columns[2])][7])+0]
                else:
                    print("This line has not application %s" % columns)
    for line in library.values():
        print(line[2])
#        columns = line.split()
#    
#        if line.startswith("Tapelibrary"):    
#            if tapename != None
#          
#                record = record + [{"measurement": "drives", "tags": {"system": args['name'], "resource_type": args['resources_types'], "host": hostname, "tapename": tapename },
#                                  "fields": {"total": float(count_used+count_unused+count_another_state), "used": float(count_used), "other": float(count_another_state)},
#                                  "time": timestamp}]
#    
#                print("tapename %s total drives %s used %s unused %s other %s" % (tapename, count_used+count_unused+count_another_state, count_used, count_unused, count_another_state))
#                count_unused = 0
#                count_used = 0
#                count_another_state = 0
#                tapename = str(columns[1])
#            else:
#                tapename = str(columns[1])
#        elif line.startswith("PLS") or line.startswith("pos"):
#            continue
#        else:
#            if str(columns[2]) == "unused":
#                count_unused = count_unused + 1
#            elif str(columns[2]) == "occupied":
#                count_used = count_used + 1
#            else:
#                count_another_state = count_another_state + 1
#    
#    record = record + [{"measurement": "drives", "tags": {"system": args['name'], "resource_type": args['resources_types'], "host": hostname, "tapename": tapename },
#                                  "fields": {"total": float(count_used+count_unused+count_another_state), "used": float(count_used), "other": float(count_another_state)},
#                                  "time": timestamp}]
#    
#    print("tapename %s total drives %s used %s unused %s other %s" % (tapename, count_used+count_unused+count_another_state, count_used, count_unused, count_another_state))
#    
#    
#    print(record)
########################