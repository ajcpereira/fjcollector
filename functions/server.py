import time
from functions_core.send_influxdb import *
from functions_core.http_connect import *
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


#### POWER
#   ['Oem']['ts_fujitsu']['ChassisPowerConsumption']['CurrentPowerConsumptionW']
#   ['Oem']['Hpe']['PowerControl']['']

DEV_DEBUG = True
URI_REDFISH_CHASSIS = '/redfish/v1/Chassis/'

class REDFISH_OEM:
    FUJITSU = 'FUJITSU'
    HPE = 'Hpe'
    CONTOSO = 'Contoso'




def server_power(**args):

    # DEFINITIONS / CONSTANTS

    #REQUEST_HEADER = {'Accept': 'application/json; charset=UTF-8'}


    #If no url parameter is configured then default configuration will be considered:
    #   - protocol HTTPS
    #   - port: 443
    #   - ip: the same for the server

    host_name = check_alias(args['alias'], args['ip'])

    if args['url'] is not None:
        base_url = args['url']
    else:
        base_url = 'https://' + str(args['ip'])

    username = args['user']
    password = args['passwd']

    logging.debug(f"FUNC[{server_power.__name__}]: Arguments are url {base_url}, user {username}, pass {password}" )
    logging.debug(f"FUNC[{server_power.__name__}]: Retrieving Chassis list from URL {base_url}{URI_REDFISH_CHASSIS}")

    http_client = HttpConnect(base_url, username, password)
    response = http_client.get(URI_REDFISH_CHASSIS)

    if response is not None:
        json_res = response.json()
        chassis_members = json_res['Members']
        logging.debug(f"FUNC[{server_power.__name__}]: Chassis Members list is {chassis_members}")

        power_consumption = 0

        #For the momment we will assume that if there are several Chassis in this system, the power_consumption
        #for the system will be the sum of all the values.

        for member in chassis_members:
            uri = member['@odata.id']
            logging.debug(f"FUNC[{server_power.__name__}]: Retrieving Chassis info from URL {base_url}{uri}")
            response = http_client.get(uri)

            if response is not None:
                json_res = response.json()
                power_uri = json_res['Power']['@odata.id']
                vendor = json_res['Manufacturer']

                logging.debug(f"FUNC[{server_power.__name__}]: Retrieved Power URI is {power_uri} ")
                logging.debug(f"FUNC[{server_power.__name__}]: Retrieved Vendor name is {vendor}")

                logging.debug(
                    f"FUNC[{server_power.__name__}]: Retrieving Power info from URL {base_url}{uri}")
                response = http_client.get(power_uri)

                if response is not None:
                    json_res = response.json()
                    logging.debug(
                        f"FUNC[{server_power.__name__}]: Retrieved power information is \033[92m {json_res} \033[00m")
                    match vendor:
                        case REDFISH_OEM.FUJITSU:
                            power_consumption += json_res['Oem']['ts_fujitsu']['ChassisPowerConsumption'][
                                'CurrentPowerConsumptionW']
                            logging.debug(
                                f"FUNC[{server_power.__name__}]: Total PowerConsumedWatts is {power_consumption}")
                        case _:
                            logging.debug(
                                f"FUNC[{server_power.__name__}]: "
                                f"Reading from PowerControl is {json_res['PowerControl']}")
                            for powerC in json_res['PowerControl']:
                                power_consumption += powerC['PowerConsumedWatts']
                            logging.debug(
                                f"FUNC[{server_power.__name__}]: Total PowerConsumedWatts is {power_consumption}")
                else:
                    logging.error(
                        f"FUNC[{server_power.__name__}]: Error Retrieving Power info from URL {base_url}{uri}")
                    return -1
            else:
                logging.error(
                    f"FUNC[{server_power.__name__}]: Error Retrieving Chassis info from URL {base_url}{uri}")
                return -1

        #Write data to influx DB

        int_timestamp = int(time.time())

        influxdb_record = [
                         {"measurement": "power",
                          "tags": {"system": args['name'], "resource_type": args['resources_types'], "host": host_name},
                          "fields": {"PowerConsumedWatts": power_consumption},
                          "time": int_timestamp
                          }
                     ]

        # Send Data to InfluxDB
        send_influxdb(str(args['repository']),
                      str(args['repository_port']),
                      args['repository_api_key'],
                      args['repo_org'],
                      args['repo_bucket'],
                      influxdb_record
                    )

        http_client.close()

    else:
        logging.error(
            f"FUNC[{server_power.__name__}]: Error Retrieving Chassis list from URL {base_url}{URI_REDFISH_CHASSIS}")
        return -1



def server_temp(**args):

    # DEFINITIONS / CONSTANTS

    #REQUEST_HEADER = {'Accept': 'application/json; charset=UTF-8'}


    #If no url parameter is configured then default configuration will be considered:
    #   - protocol HTTPS
    #   - port: 443
    #   - ip: the same for the server

    host_name = check_alias(args['alias'], args['ip'])

    if args['url'] is not None:
        base_url = args['url']
    else:
        base_url = 'https://' + str(args['ip'])

    username = args['user']
    password = args['passwd']

    logging.debug(f"FUNC[{server_temp.__name__}]: Arguments are url {base_url}, user {username}, pass {password}" )
    logging.debug(f"FUNC[{server_temp.__name__}]: Retrieving Chassis list from URL {base_url}{URI_REDFISH_CHASSIS}")

    http_client = HttpConnect(base_url, username, password)
    response = http_client.get(URI_REDFISH_CHASSIS)

    if response is not None:
        json_res = response.json()
        chassis_members = json_res['Members']
        logging.debug(f"FUNC[{server_temp.__name__}]: Chassis Members list is {chassis_members}")

        power_consumption = 0

        #For the momment we will assume that if there are several Chassis in this system, the power_consumption
        #for the system will be the sum of all the values.

        for member in chassis_members:
            uri = member['@odata.id']
            logging.debug(f"FUNC[{server_temp.__name__}]: Retrieving Chassis info from URL {base_url}{uri}")
            response = http_client.get(uri)

            if response is not None:
                json_res = response.json()
                thermal_uri = json_res['Thermal']['@odata.id']
                vendor = json_res['Manufacturer']

                logging.debug(f"FUNC[{server_temp.__name__}]: Retrieved Thermal URI is {thermal_uri} ")
                logging.debug(f"FUNC[{server_temp.__name__}]: Retrieved Vendor name is {vendor}")

                logging.debug(
                    f"FUNC[{server_temp.__name__}]: Retrieving Thermal info from URL {base_url}{uri}")
                response = http_client.get(thermal_uri)

                if response is not None:
                    json_res = response.json()
                    logging.debug(
                        f"FUNC[{server_temp.__name__}]: Retrieved Thermal information is \033[92m {json_res} \033[00m")

                    intake_temp = None
                    for temp in json_res['Temperatures']:
                        if temp['PhysicalContext'] == "Intake":
                            intake_temp = temp['ReadingCelsius']
                            break
                    logging.debug(
                        f"FUNC[{server_temp.__name__}]: Intake Temperature is {intake_temp}")

                else:
                    logging.error(
                        f"FUNC[{server_temp.__name__}]: Error Retrieving Thermal info from URL {base_url}{uri}")
                    return -1
            else:
                logging.error(
                    f"FUNC[{server_temp.__name__}]: Error Retrieving Chassis info from URL {base_url}{uri}")
                return -1

        #Write data to influx DB

        int_timestamp = int(time.time())

        influxdb_record = [
                         {"measurement": "temp",
                          "tags": {"system": args['name'], "resource_type": args['resources_types'], "host": host_name},
                          "fields": {"AmbTemp": intake_temp},
                          "time": int_timestamp
                          }
                     ]

        # Send Data to InfluxDB
        send_influxdb(str(args['repository']),
                      str(args['repository_port']),
                      args['repository_api_key'],
                      args['repo_org'],
                      args['repo_bucket'],
                      influxdb_record
                    )

        http_client.close()

    else:
        logging.error(
            f"FUNC[{server_temp.__name__}]: Error Retrieving Chassis list from URL {base_url}{URI_REDFISH_CHASSIS}")
        return -1




def check_alias(alias, ip):
    # Check if Alias is defined, if not use IPAddress for hostname
    if alias:
        hostname = alias
    else:
        hostname = ip

    return hostname
