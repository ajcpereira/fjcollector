from grafanalib.core import *
from grafanalib.influxdb import *
from grafanalib._gen import DashboardEncoder
import json, requests, logging
from functions_core.yaml_validate import *


def get_dashboard_json(dashboard, overwrite=False, message="Updated by grafanlib"):
    '''
    get_dashboard_json generates JSON from grafanalib Dashboard object

    :param dashboard - Dashboard() created via grafanalib
    '''

    # grafanalib generates json which need to pack to "dashboard" root element
    return json.dumps(
        {
            "dashboard": dashboard.to_json_data(),
            "overwrite": overwrite,
            "message": message
        }, sort_keys=True, indent=2, cls=DashboardEncoder)


def upload_to_grafana(json_data, server, api_key, verify=True):
    '''
    upload_to_grafana tries to upload dashboard to grafana and prints response

    :param json_data - dashboard json generated by grafanalib
    :param server - grafana server name
    :param api_key - grafana api key with read and write privileges
    '''

    headers = {'Authorization': f"Bearer {api_key}", 'Content-Type': 'application/json'}

    try:
        r = requests.post(f"http://{server}/api/dashboards/db", data=json_data, headers=headers, verify=verify)
        logging.debug("Message from fungraph %s" % r.json() )
    except Exception as msgerror:
        logging.error("Failed to create report in grafana %s with error %s" % (server, msgerror))


def create_system_dashboard(sys, config):
    panels = []

    for res in sys['resources']:
        match res['name']:
            case "linux_os":
                panels = panels + create_panel_linux_os(str(sys['system']), str(res['name']), res['data'], sys['poll'])
            case "eternus_cs8000":
                panels = panels + create_panel_eternus_cs8000(str(sys['system']), str(res['name']), res['data'],sys['poll'])

    my_dashboard = Dashboard(
        title="System " + sys['system'] + " dashboard",
        description="fj-collector auto generated dashboard",
        tags=[
            sys['system'],
        ],
        timezone="browser",
        refresh="1m",
        panels=panels,

    ).auto_panel_ids()

    return my_dashboard


########################################################################################################################
#
# function: build_dashboards
#
# This function builds a grafana dashboard based on the monitored items, configured on the config.yaml file.
########################################################################################################################

def build_dashboards(config):
    # Dashboards will not be overwrited anymore

    logging.debug("Will build dashboards")
    grafana_api_key = config.global_parameters.grafana_api_key
    grafana_server = config.global_parameters.grafana_server + ":3000"

    systems = build_grafana_fun_data_model(config)

    for sys in systems:
        my_dashboard = create_system_dashboard(sys, config)
        my_dashboard_json = get_dashboard_json(my_dashboard, overwrite=False, message="Updated by fj-collector")
        logging.debug("Created dashboard %s", my_dashboard_json)
        upload_to_grafana(my_dashboard_json, grafana_server, grafana_api_key)


########################################################################################################################
#
# function: build_grafana_fun_data_model
#
# This function builds a dictionary with the data model for creating the graphs
# This functions need rework!!!!!
########################################################################################################################


def build_grafana_fun_data_model(config):
    def check_if_metric_exists(system_name, resource_name, metric_name, lst):
        metrics_lst = []
        b_exists = False

        for x in lst:
            if system_name in x['system']:
                for y in x['resources']:
                    if resource_name == y['name']:
                        for z in y['data']:
                            if metric_name == z['metric']:
                                metrics_lst = z['hosts']
                                b_exists = True

        return b_exists, metrics_lst

    def check_if_system_exists(system_name, lst):

        b_result = False
        for x in lst:
            if system_name == x['system']:
                b_result = True

        return b_result

    def check_if_resource_exists(system_name, resource_name, lst):

        b_result = False
        for x in lst:
            if system_name == x['system']:
                for y in x['resources']:
                    if resource_name == y['name']:
                        b_result = True

        return b_result

    def my_update_resource_list(system_name, resource_name, metric_name, lst, dict_metric):

        for x in lst:
            if system_name == x['system']:
                for y in x['resources']:
                    if resource_name == y['name']:
                        for k in y['data']:
                            if metric_name == k['metric']:
                                k.update(dict_metric)

        return lst

    def add_resource(system_name, dict, model):

        local_model = model

        for x in local_model:
            if system_name in x['system']:
                x['resources'].append(dict)
                logging.debug(add_resource.__name__ + ": existing resources are %s", x)

        logging.debug(add_resource.__name__ + ": function result is %s", local_model)

        return local_model

    def my_add_metrics_to_existing_resource_list(system_name, resource_name, dict_metric, model):

        local_model = model

        for x in local_model:
            if system_name == x['system']:
                for y in x['resources']:
                    if resource_name == y['name']:
                        y['data'].append(dict_metric[0])

        return local_model

    logging.debug(build_grafana_fun_data_model.__name__ + ": Config data is - %s", config)
    model_result = []

    try:
        for system in config.systems:
            metric_list = []
            res_list = []
            met_exists = False
            for metric in system.config.metrics:
                host_list = []
                for ip in system.config.ips:
                    #if not ip.alias is None:
                    if ip.alias is not None:
                        hostname = ip.alias
                    else:
                        hostname = str(ip.ip)
                    host_list.append(hostname)

                met_exists, met_hosts_lst = check_if_metric_exists(system.name, system.resources_types, metric.name,
                                                                   model_result)
                logging.debug(build_grafana_fun_data_model.__name__ + ": Existing metric %s and hosts %s", metric.name,
                              met_hosts_lst)
                logging.debug(build_grafana_fun_data_model.__name__ + ": Adding metric %s and hosts %s", metric.name,
                              host_list)
                if met_exists:
                    metric_dict = {"metric": metric.name, "hosts": met_hosts_lst + host_list}
                    logging.debug(build_grafana_fun_data_model.__name__ + ": New metric list %s ",
                                  metric_dict)

                    model_result = my_update_resource_list(system.name, system.resources_types, metric.name,
                                                           model_result, metric_dict)
                    logging.debug(build_grafana_fun_data_model.__name__ + ": New model result %s ",
                                  model_result)
                else:
                    metric_list.append({"metric": metric.name, "hosts": host_list})

                logging.debug(build_grafana_fun_data_model.__name__ + ": Metrics exist %s and metrics list is %s",
                              met_exists, metric_list)

            res_exists = check_if_resource_exists(system.name, system.resources_types, model_result)

            if res_exists and not met_exists:
                logging.debug(
                    build_grafana_fun_data_model.__name__ +
                    ": Resource exist=%s and metrics exist=%s metrics list is %s model_result %s",
                    res_exists, met_exists, metric_list, model_result)
                model_result = my_add_metrics_to_existing_resource_list(system.name, system.resources_types,
                                                                        metric_list, model_result)

            if not res_exists:
                logging.debug(
                    build_grafana_fun_data_model.__name__ + ": Resource %s do not exists but system %s exists",
                    system.resources_types, system.name)
                res_list.append({"name": system.resources_types, "data": metric_list})

            if check_if_system_exists(system.name, model_result) and not res_exists:
                logging.debug(build_grafana_fun_data_model.__name__ + ": System exists - %s", model_result)
                model_result = add_resource(system.name, {"name": system.resources_types, "data": metric_list},
                                            model_result)

            # System
            if not check_if_system_exists(system.name, model_result) and not res_exists:
                model_result.append(
                    {"system": system.name, "resources": res_list, "poll": system.config.parameters.poll})

            logging.debug(build_grafana_fun_data_model.__name__ + ": Model is - %s", model_result)
    except Exception as msgerror:
        logging.error(
            build_grafana_fun_data_model.__name__ +
            ": Unexpected error creating grafana_fun data model - %s" % msgerror)
        return -1

    logging.debug(build_grafana_fun_data_model.__name__ + ": grafana_fun data model is - %s", model_result)

    return model_result


########################################################################################################################
#
# Resource Type: linux_os
#
########################################################################################################################


def create_panel_linux_os(system_name, resource_name, data, poll):
    # todo:

    panels_list = []

    for metric in data:
        match metric['metric']:
            case "cpu":
                panels_list.append(RowPanel(title=resource_name + ': CPU', gridPos=GridPos(h=1, w=24, x=0, y=0)))

                panels_target_list_cpu_use = []
                for host in metric['hosts']:
                    panels_target_list_cpu_use = panels_target_list_cpu_use + [InfluxDBTarget(
                        query="SELECT \"use\" FROM \"cpu\" WHERE $timeFilter AND (\"host\"::tag = '" + host +
                              "') AND (\"system\"::tag = '" + system_name + "') GROUP BY \"host\"::tag",
                        alias="$tag_host").to_json_data()]

                panels_list.append(TimeSeries(
                    title="CPU utilization (%)",
                    dataSource='default',
                    targets=panels_target_list_cpu_use,
                    drawStyle='line',
                    lineInterpolation='smooth',
                    gradientMode='hue',
                    fillOpacity=25,
                    unit="percent",
                    gridPos=GridPos(h=7, w=12, x=0, y=1),
                    spanNulls=True,
                    legendPlacement="right",
                    legendDisplayMode="table"
                ))

                panels_target_list_cpu_load = []
                for host in metric['hosts']:
                    panels_target_list_cpu_load = panels_target_list_cpu_load + [InfluxDBTarget(
                        query="SELECT \"load5m\" FROM \"cpu\" WHERE $timeFilter AND (\"host\"::tag = '" + host +
                              "') AND (\"system\"::tag = '" + system_name + "') GROUP BY \"host\"::tag",
                        alias="$tag_host")]

                panels_list.append(TimeSeries(
                    title="CPU Average Load (5 min)",
                    dataSource='default',
                    targets=panels_target_list_cpu_load,
                    drawStyle='line',
                    lineInterpolation='smooth',
                    gradientMode='hue',
                    fillOpacity=25,
                    unit="",
                    gridPos=GridPos(h=7, w=12, x=12, y=1),
                    spanNulls=True,
                    legendPlacement="right",
                    legendDisplayMode="table"
                ))
            case "mem":

                panels_list.append(RowPanel(title=resource_name + ': Memory', gridPos=GridPos(h=1, w=24, x=0, y=2)))

                target_mem = [InfluxDBTarget(
                    query="SELECT  (total)-(avail) as \"Used\", (avail) as \"Available\" FROM \"mem\" WHERE $timeFilter AND (\"system\"::tag = '" + system_name + "') GROUP BY \"host\"::tag ORDER BY time DESC LIMIT 1",
                    format="table")]

                panels_list.append(BarChart(
                    title="Memory Usage",
                    dataSource='default',
                    targets=target_mem,
                    drawStyle='line',
                    lineInterpolation='smooth',
                    gradientMode='hue',
                    fillOpacity=25,
                    unit="decmbytes",
                    gridPos=GridPos(h=7, w=24, x=0, y=3),
                    spanNulls=True,
                    legendPlacement="right",
                    legendDisplayMode="table",
                    stacking={'mode': "normal"},
                    tooltipMode="multi",
                ))

            case "fs":
                panels_list.append(
                    RowPanel(title=resource_name + ': File System', gridPos=GridPos(h=1, w=24, x=0, y=4)))

                for host in metric['hosts']:
                    target_fs = [InfluxDBTarget(
                        query="SELECT \"used\" as Used, \"total\"-\"used\" as Available FROM \"fs\" WHERE $timeFilter AND (\"host\"::tag = '" + host + "') AND (\"system\"::tag = '" + system_name + "') GROUP BY \"mount\"::tag ORDER BY time DESC LIMIT 1",
                        format="table")]

                    panels_list.append(BarChart(
                        title=host + " Filesystem",
                        dataSource='default',
                        targets=target_fs,
                        drawStyle='line',
                        lineInterpolation='smooth',
                        gradientMode='hue',
                        fillOpacity=25,
                        unit="deckbytes",
                        gridPos=GridPos(h=7, w=24, x=0, y=5),
                        spanNulls=True,
                        legendPlacement="right",
                        legendDisplayMode="table",
                        stacking={'mode': "normal"},
                        tooltipMode="multi",
                        xTickLabelRotation=-45,
                    ))

            case "net":
                panels_list.append(RowPanel(title=resource_name + ': Network', gridPos=GridPos(h=1, w=24, x=0, y=6)))
                for host in metric['hosts']:
                    target_net_outbound = [InfluxDBTarget(
                        query="SELECT derivative(\"tx_bytes\", " + str(poll) +
                              "m) FROM \"net\" WHERE (\"host\"::tag = '" + host + "') AND (\"system\"::tag = '" +
                              system_name + "') AND $timeFilter GROUP BY \"if\"::tag",
                        alias="$tag_if")]

                    panels_list.append(TimeSeries(
                        title=host + " Network Outbound",
                        dataSource='default',
                        targets=target_net_outbound,
                        drawStyle='line',
                        lineInterpolation='smooth',
                        gradientMode='hue',
                        fillOpacity=25,
                        unit="binBps",
                        gridPos=GridPos(h=7, w=12, x=0, y=7),
                        spanNulls=True,
                        legendPlacement="right",
                        legendDisplayMode="table"
                    ))

                    target_net_inbound = [InfluxDBTarget(
                        query="SELECT derivative(\"rx_bytes\"," + str(poll) +
                              "m) FROM \"net\" WHERE (\"host\"::tag = '" + host + "') AND (\"system\"::tag = '" +
                              system_name + "')  AND $timeFilter GROUP BY \"if\"::tag",
                        alias="$tag_if")]

                    panels_list.append(TimeSeries(
                        title=host + " Network Inbound",
                        dataSource='default',
                        targets=target_net_inbound,
                        drawStyle='line',
                        lineInterpolation='smooth',
                        gradientMode='hue',
                        fillOpacity=25,
                        unit="binBps",
                        gridPos=GridPos(h=7, w=12, x=12, y=7),
                        spanNulls=True,
                        legendPlacement="right",
                        legendDisplayMode="table"
                    ))

    return panels_list


########################################################################################################################
#
# Resource Type: eternus_cs8000
#
########################################################################################################################

def create_panel_eternus_cs8000(system_name, resource_name, data, poll):
    panels_list = []

    for metric in data:
        match metric['metric']:
            case "fs_io":
                panels_list.append(
                    RowPanel(title=resource_name + ': CAFS IOSTAT', gridPos=GridPos(h=1, w=24, x=0, y=8)))

                for host in metric['hosts']:
                    panels_target_list = [InfluxDBTarget(
                        query="SELECT \"svctm\" FROM \"fs_io\" WHERE (\"host\"::tag = '" + host +
                              "') AND (\"system\"::tag = '" + system_name +
                              "') AND $timeFilter GROUP BY \"fs\"::tag, \"dm\"::tag, \"rawdev\"::tag",
                        alias="$tag_fs $tag_dm $tag_rawdev")]

                    panels_list.append(TimeSeries(
                        title=host + " SVCTM",
                        dataSource='default',
                        targets=panels_target_list,
                        drawStyle='line',
                        lineInterpolation='smooth',
                        gradientMode='hue',
                        fillOpacity=25,
                        unit="ms",
                        gridPos=GridPos(h=7, w=8, x=0, y=9),
                        spanNulls=True,
                        legendPlacement="right",
                        legendDisplayMode="table"
                    ))

                    panels_target_list = [InfluxDBTarget(
                        query="SELECT \"r_await\" FROM \"fs_io\" WHERE (\"host\"::tag = '" + host +
                              "') AND (\"system\"::tag = '" + system_name +
                              "')  AND $timeFilter GROUP BY \"fs\"::tag, \"dm\"::tag, \"rawdev\"::tag",
                        alias="$tag_fs $tag_dm $tag_rawdev")]

                    panels_list.append(TimeSeries(
                        title=host + " R_AWAIT",
                        dataSource='default',
                        targets=panels_target_list,
                        drawStyle='line',
                        lineInterpolation='smooth',
                        gradientMode='hue',
                        fillOpacity=25,
                        unit="ms",
                        gridPos=GridPos(h=7, w=8, x=8, y=10),
                        spanNulls=True,
                        legendPlacement="right",
                        legendDisplayMode="table"
                    ))

                    panels_target_list = [InfluxDBTarget(
                        query="SELECT \"w_await\" FROM \"fs_io\" WHERE (\"host\"::tag = '" + host +
                              "') AND (\"system\"::tag = '" + system_name +
                              "') AND $timeFilter GROUP BY \"fs\"::tag, \"dm\"::tag, \"rawdev\"::tag",
                        alias="$tag_fs $tag_dm $tag_rawdev")]

                    panels_list.append(TimeSeries(
                        title=host + " W_AWAIT",
                        dataSource='default',
                        targets=panels_target_list,
                        drawStyle='line',
                        lineInterpolation='smooth',
                        gradientMode='hue',
                        fillOpacity=25,
                        unit="ms",
                        gridPos=GridPos(h=7, w=8, x=16, y=11),
                        spanNulls=True,
                        legendPlacement="right",
                        legendDisplayMode="table"
                    ))
            case "cpu":
                panels_list.append(RowPanel(title=resource_name + ': CPU', gridPos=GridPos(h=1, w=24, x=0, y=0)))

                panels_target_list_cpu_use = []
                for host in metric['hosts']:
                    panels_target_list_cpu_use = panels_target_list_cpu_use + [InfluxDBTarget(
                        query="SELECT \"use\" FROM \"cpu\" WHERE $timeFilter AND (\"host\"::tag = '" + host +
                              "') AND (\"system\"::tag = '" + system_name + "') GROUP BY \"host\"::tag",
                        alias="$tag_host").to_json_data()]

                panels_list.append(TimeSeries(
                    title="CPU utilization (%)",
                    dataSource='default',
                    targets=panels_target_list_cpu_use,
                    drawStyle='line',
                    lineInterpolation='smooth',
                    gradientMode='hue',
                    fillOpacity=25,
                    unit="percent",
                    gridPos=GridPos(h=7, w=12, x=0, y=1),
                    spanNulls=True,
                    legendPlacement="right",
                    legendDisplayMode="table"
                ))

                panels_target_list_cpu_load = []
                for host in metric['hosts']:
                    panels_target_list_cpu_load = panels_target_list_cpu_load + [InfluxDBTarget(
                        query="SELECT \"load5m\" FROM \"cpu\" WHERE $timeFilter AND (\"host\"::tag = '" + host + "') AND (\"system\"::tag = '" + system_name + "') GROUP BY \"host\"::tag",
                        alias="$tag_host")]

                panels_list.append(TimeSeries(
                    title="CPU Average Load (5 min)",
                    dataSource='default',
                    targets=panels_target_list_cpu_load,
                    drawStyle='line',
                    lineInterpolation='smooth',
                    gradientMode='hue',
                    fillOpacity=25,
                    unit="",
                    gridPos=GridPos(h=7, w=12, x=12, y=1),
                    spanNulls=True,
                    legendPlacement="right",
                    legendDisplayMode="table"
                ))
            case "mem":

                panels_list.append(RowPanel(title=resource_name + ': Memory', gridPos=GridPos(h=1, w=24, x=0, y=2)))

                target_mem = [InfluxDBTarget(
                    query="SELECT  (total)-(avail) as \"Used\", (avail) as \"Available\" FROM \"mem\" WHERE $timeFilter AND (\"system\"::tag = '" + system_name + "') GROUP BY \"host\"::tag ORDER BY time DESC LIMIT 1",
                    format="table")]

                panels_list.append(BarChart(
                    title="Memory Usage",
                    dataSource='default',
                    targets=target_mem,
                    drawStyle='line',
                    lineInterpolation='smooth',
                    gradientMode='hue',
                    fillOpacity=25,
                    unit="decmbytes",
                    gridPos=GridPos(h=7, w=24, x=0, y=3),
                    spanNulls=True,
                    legendPlacement="right",
                    legendDisplayMode="table",
                    stacking={'mode': "normal"},
                    tooltipMode="multi",
                ))

            case "fs":
                panels_list.append(
                    RowPanel(title=resource_name + ': File System', gridPos=GridPos(h=1, w=24, x=0, y=4)))

                for host in metric['hosts']:
                    target_fs = [InfluxDBTarget(
                        query="SELECT \"used\" as Used, \"total\"-\"used\" as Available FROM \"fs\" WHERE $timeFilter AND (\"host\"::tag = '" + host + "') AND (\"system\"::tag = '" + system_name + "') GROUP BY \"mount\"::tag ORDER BY time DESC LIMIT 1",
                        format="table")]

                    panels_list.append(BarChart(
                        title=host + " Filesystem",
                        dataSource='default',
                        targets=target_fs,
                        drawStyle='line',
                        lineInterpolation='smooth',
                        gradientMode='hue',
                        fillOpacity=25,
                        unit="deckbytes",
                        gridPos=GridPos(h=7, w=24, x=0, y=5),
                        spanNulls=True,
                        legendPlacement="right",
                        legendDisplayMode="table",
                        stacking={'mode': "normal"},
                        tooltipMode="multi",
                        xTickLabelRotation=-45,
                    ))

            case "net":
                panels_list.append(RowPanel(title=resource_name + ': Network', gridPos=GridPos(h=1, w=24, x=0, y=6)))
                for host in metric['hosts']:
                    target_net_outbound = [InfluxDBTarget(
                        query="SELECT derivative(\"tx_bytes\", " + str(poll) +
                              "m) FROM \"net\" WHERE (\"host\"::tag = '" + host +
                              "') AND $timeFilter GROUP BY \"if\"::tag",
                        alias="$tag_if")]

                    panels_list.append(TimeSeries(
                        title=host + " Network Outbound",
                        dataSource='default',
                        targets=target_net_outbound,
                        drawStyle='line',
                        lineInterpolation='smooth',
                        gradientMode='hue',
                        fillOpacity=25,
                        unit="binBps",
                        gridPos=GridPos(h=7, w=12, x=0, y=7),
                        spanNulls=True,
                        legendPlacement="right",
                        legendDisplayMode="table"
                    ))

                    target_net_inbound = [InfluxDBTarget(
                        query="SELECT derivative(\"rx_bytes\"," + str(
                            poll) + "m) FROM \"net\" WHERE (\"host\"::tag = '" + host + "') AND $timeFilter GROUP BY \"if\"::tag",
                        alias="$tag_if")]

                    panels_list.append(TimeSeries(
                        title=host + " Network Inbound",
                        dataSource='default',
                        targets=target_net_inbound,
                        drawStyle='line',
                        lineInterpolation='smooth',
                        gradientMode='hue',
                        fillOpacity=25,
                        unit="binBps",
                        gridPos=GridPos(h=7, w=12, x=12, y=7),
                        spanNulls=True,
                        legendPlacement="right",
                        legendDisplayMode="table"
                    ))

    return panels_list


# Grafanalib doesn't have a class to manipulate BarChart
# this is a new class, based on TimeSeries class, to create BarChart graphs
@attr.s
class BarChart(TimeSeries):

    def __init__(self, xTickLabelRotation, **kwargs):
        super().__init__(self, **kwargs)
        self.xTickLabelRotation = xTickLabelRotation

    xTickLabelRotation = attr.ib(default=0, validator=instance_of(int))

    def to_json_data(self):
        return self.panel_json(
            {
                'fieldConfig': {
                    'defaults': {
                        'color': {
                            'mode': self.colorMode
                        },
                        'custom': {
                            'axisPlacement': self.axisPlacement,
                            'axisLabel': self.axisLabel,
                            'drawStyle': self.drawStyle,
                            'lineInterpolation': self.lineInterpolation,
                            'barAlignment': self.barAlignment,
                            'lineWidth': self.lineWidth,
                            'fillOpacity': self.fillOpacity,
                            'gradientMode': self.gradientMode,
                            'spanNulls': self.spanNulls,
                            'showPoints': self.showPoints,
                            'pointSize': self.pointSize,
                            'scaleDistribution': {
                                'type': self.scaleDistributionType,
                                'log': self.scaleDistributionLog
                            },
                            'hideFrom': {
                                'tooltip': False,
                                'viz': False,
                                'legend': False
                            },
                            'thresholdsStyle': {
                                'mode': self.thresholdsStyleMode
                            },
                        },
                        'mappings': self.mappings,
                        'unit': self.unit
                    },
                    'overrides': self.overrides
                },
                'options': {
                    'stacking': self.stacking,
                    'xTickLabelRotation': self.xTickLabelRotation,
                    'legend': {
                        'displayMode': self.legendDisplayMode,
                        'placement': self.legendPlacement,
                        'calcs': self.legendCalcs
                    },
                    'tooltip': {
                        'mode': self.tooltipMode
                    }
                },
                'type': "barchart",
            })
