########################################################################################################################
#  DO NOT USE!!! UNDER DEVELOPMENT!!!
#
#   name: grafun_cli
#   usage:
# usage: grafun-cli.py [-h] [--server SERVER] [--config-file CONFIG_FILE] [--api-token API_TOKEN] [--dashboard-name DASHBOARD_NAME]
#
# Grafana Dashboard Configuration
#
# options:
#   -h, --help            show this help message and exit
#   --server SERVER       Grafana server URL, if none is specified use from config file
#   --config-file CONFIG_FILE
#                         Path to custom configuration file
#   --api-token API_TOKEN
#                         Grafana API token, if none is specified use from config file
#   --dashboard-name DASHBOARD_NAME
#                         Name of the Grafana dashboard, if none is specified use automated name
#
#
########################################################################################################################


VERSION = 0.5

import yaml
import json, requests, logging
import functions_core.yaml_validate
import argparse
from functions_core.grafana_fun import *


def new_create_system_dashboard(sys, dash_name=None):
    panels = []
    templating = []
    y_pos = 3

    if dash_name is None:
        dash_name = f"System {sys['system']} dashboard"
    else:
        dash_name = dash_name + f" {sys['system']}"

    panels = panels + create_title_panel(str(sys['system']))

    for res in sys['resources']:
        match res['name']:
            case "linux_os":
                y_pos, res_panel = graph_linux_os(str(sys['system']), str(res['name']), res['data'], y_pos)
                panels = panels + res_panel
            case "eternus_cs8000":
                y_pos, res_panel = graph_eternus_cs8000(str(sys['system']), str(res['name']), res['data'], y_pos)
                templating = create_dashboard_vars(res['data'])
                panels = panels + res_panel

    my_dashboard = Dashboard(
        title=dash_name,
        description="fjcollector auto generated dashboard",
        tags=[
            sys['system'],
        ],
        timezone="browser",
        refresh="1m",
        panels=panels,
        templating=Templating(templating),
    ).auto_panel_ids()

    return my_dashboard


def new_build_dashboards(config, grafana_url=None, grafana_token=None, dash_name=None):
    """
    Creates a Grafana dashboard using the provided parameters.

    Args:
        config (object, optional): The configuration file object (default is None).
        grafana_url (str, optional): The Grafana server URL (default is "localhost:3000").
        dash_name (str, optional): The name of the dashboard (default is "Default Dashboard").
        grafana_token (str, optional): The JWT token for authentication (default is None).

    Returns:
        str: A message indicating the successful creation of the dashboard.
    """
    # Your implementation here
    # ...
    if grafana_url is None:
        grafana_url = config.global_parameters.grafana_server + ":3000"

    if grafana_token is None:
        grafana_token = config.global_parameters.grafana_api_key

    systems = data_model_build(config)

    for sys_item in systems:
        print(f"Creating Dashboard for system: {sys_item['system']}")
        my_dashboard = new_create_system_dashboard(sys_item, dash_name)
        my_dashboard_json = get_dashboard_json(my_dashboard, overwrite=True, message="Updated by grafun-cli")
        logging.debug("Created dashboard %s", my_dashboard_json)
        res = upload_to_grafana(my_dashboard_json, grafana_url, grafana_token)
        if res is not None:
            if res.status_code == 200:
                print(f"Dashboard for system {sys_item['system']} created ({res.status_code} {res.reason})")
            else:
                print(f"Unable to create dashboard for system {sys_item['system']} error is: {res.status_code} {res.reason}")
        else:
            print(f"Unexpected error occurred!!!")

    # return f"{grafana_url} Dashboard '{dash_name}' created successfully!"


def parse_args():
    parser = argparse.ArgumentParser(description="Grafana Dashboard Configuration")
    parser.add_argument("--server", default=None, help="Grafana server URL, if none is specified use from config file")
    parser.add_argument("--config-file", default="config/config.yaml", help="Path to custom configuration file")
    parser.add_argument("--api-token", default=None,
                        help="Grafana API token, if none is specified use from config file")
    parser.add_argument("--dashboard-name", default=None, help="Name of the Grafana dashboard, if none is "
                                                               "specified use automated name")
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"Grafana command line dashboard creator v{VERSION}")
    print(f"Type -h for help.")
    print()
    print(f"Parameters:")

    if args.config_file != "config/config.yaml":
        print(f"  Config File: {args.config_file}")

    if args.server is not None:
        print(f"  Grafana Server: {args.server}")

    if args.api_token is not None:
        print(f"  API Token: {args.api_token}")

    print()

    # Read from config file
    print(f"Reading from config File: {args.config_file}")

    # Read configration file
    config, orig_mtime, configfile_running = configfile_read(args.config_file)

    # Check if consistent
    result_dicts, global_parms = create_metric_ip_dicts(config)

    # Get Grafana server from config file
    # if args.server is None:
    #     args.server = config.global_parameters.grafana_server
    #     print(f"  Grafana Server from config file: {args.server}")

    # Get Grafana API Token
    # if args.api_token is None:
    #     args.api_token = config.global_parameters.grafana_api_key
    #     print(f"  API Token from config file: {args.api_token}")

    # Check Data Model
    print(f"Building Data Model...")
    systems = data_model_build(config)

    i = 0
    str_sysname = ""
    for sys in systems:
        i += 1
        str_sysname += f"{sys['system']} "

    print(f"Found {i} system(s): {str_sysname}")

    new_build_dashboards(config, args.server, args.api_token, args.dashboard_name)

    # new_build_dashboards(config)


if __name__ == "__main__":
    main()
