
import json, requests, logging
from functions_core.yaml_validate import *
from functions_core.grafanafun_dm import data_model_build
from functions_core.grafanalib_ext import *
from grafanalib._gen import DashboardEncoder


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
        logging.debug("Message from grafana_fun is %s" % r.json())
    except Exception as msgerror:
        logging.error("Failed to create report in grafana %s with error %s" % (server, msgerror))


def create_system_dashboard(sys, config):
    panels = []
    templating = []
    y_pos = 3

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
        title="System " + sys['system'] + " dashboard",
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


########################################################################################################################
#
# function: build_dashboards
#
# This function builds a grafana dashboard based on the monitored items, configured on the config.yaml file.
########################################################################################################################

def build_dashboards(config):
    # Dashboards will be overwritten

    logging.debug("%s: Automagically build grafana dashboards", build_dashboards.__name__)
    grafana_api_key = config.global_parameters.grafana_api_key
    grafana_server = config.global_parameters.grafana_server + ":3000"

    # systems = build_grafana_fun_data_model(config)
    systems = data_model_build(config)

    for sys in systems:
        my_dashboard = create_system_dashboard(sys, config)
        my_dashboard_json = get_dashboard_json(my_dashboard, overwrite=True, message="Updated by fjcollector")
        logging.debug("Created dashboard %s", my_dashboard_json)
        upload_to_grafana(my_dashboard_json, grafana_server, grafana_api_key)


########################################################################################################################
#
# Resource Type: linux_os
#
########################################################################################################################


def graph_linux_os(system_name, resource_name, data, global_pos):
    # todo:

    panels_list = []
    y_pos = global_pos

    for metric in data:
        match metric['metric']:
            case "cpu":
                y_pos, panel = graph_linux_os_cpu(system_name, resource_name, metric, y_pos)
                panels_list = panels_list + panel

            case "mem":
                y_pos, panel = graph_linux_os_mem(system_name, resource_name, y_pos)
                panels_list = panels_list + panel

            case "fs":
                y_pos, panel = graph_linux_os_fs(system_name, resource_name, metric, y_pos)
                panels_list = panels_list + panel

            case "net":
                y_pos, panel = graph_linux_os_net(system_name, resource_name, metric, y_pos)
                panels_list = panels_list + panel

    return y_pos, panels_list


########################################################################################################################
#
# Resource Type: eternus_cs8000
#
########################################################################################################################

def graph_eternus_cs8000(system_name, resource_name, data, global_pos):
    panels_list = []
    y_pos = global_pos

    for metric in data:
        match metric['metric']:
            case "fs_io":
                y_pos, panel = graph_eternus_cs8000_fs_io(system_name, resource_name, metric, y_pos)
                panels_list = panels_list + panel

            case "drives":
                y_pos, panel = graph_eternus_cs8000_drives(system_name, resource_name, y_pos)
                panels_list = panels_list + panel

            case "medias":
                y_pos, panel = graph_eternus_cs8000_medias(system_name, resource_name, y_pos)
                panels_list = panels_list + panel

            case "pvgprofile":
                y_pos, panel = graph_eternus_cs8000_pvgprofile(system_name, resource_name, y_pos)
                panels_list = panels_list + panel

            case "fc":
                y_pos, panel = graph_eternus_cs8000_fc(system_name, resource_name, metric, y_pos)
                panels_list = panels_list + panel

            case "cpu":
                y_pos, panel = graph_linux_os_cpu(system_name, resource_name, metric, y_pos)
                panels_list = panels_list + panel

            case "mem":
                y_pos, panel = graph_linux_os_mem(system_name, resource_name, y_pos)
                panels_list = panels_list + panel

            case "fs":
                y_pos, panel = graph_linux_os_fs(system_name, resource_name, metric, y_pos)
                panels_list = panels_list + panel

            case "net":
                y_pos, panel = graph_linux_os_net(system_name, resource_name, metric, y_pos)
                panels_list = panels_list + panel

    return y_pos, panels_list


########################################################################################################################
#
# Resource Type: create_title_panel
#
########################################################################################################################
def create_title_panel(system_name):
    str_msg = "<br><p style=\"text-align:center\"><span style=\"font-size:36px\">System " + system_name + "</span></p>"

    panel = [Text(
        title="",
        gridPos=GridPos(h=3, w=24, x=0, y=0),
        mode="html",
        content=str_msg,
    )]

    return panel


def create_dashboard_vars(data):
    tpl_lst = []

    for metric in data:
        match metric['metric']:
            case "drives":
                tpl_lst = tpl_lst + [Template(
                    # dataSource="default",
                    name='tapename',
                    label='tapename',
                    query='SHOW TAG VALUES WITH KEY = \"tapename\"',
                    type='query',
                    includeAll=True,
                    multi=True,
                    allValue=True,
                    default='All',
                    refresh=2,
                    hide=HIDE_VARIABLE,
                    )
                ]

    return tpl_lst


def graph_linux_os_cpu(system_name, resource_name, metric, y_pos):

    str_title = "CPU Usage (" + resource_name + ")"
    panels_list = [RowPanel(title=str_title, gridPos=GridPos(h=1, w=24, x=0, y=y_pos))]
    line = y_pos + 1

    panels_target_list_cpu_use = []
    panels_target_list_cpu_load = []
    for host in metric['hosts']:
        panels_target_list_cpu_use = panels_target_list_cpu_use + [InfluxDBTarget(
            query="SELECT mean(\"use\") FROM \"cpu\" WHERE (\"system\"::tag = '" + system_name +
                  "' AND \"host\"::tag = '" + host + "') AND $timeFilter GROUP BY time($__interval), \"host\"::tag fill(null)",
            alias="$tag_host")]
        panels_target_list_cpu_load = panels_target_list_cpu_load + [InfluxDBTarget(
            query="SELECT \"load5m\" FROM \"cpu\" WHERE (\"system\"::tag = '" + system_name +
                  "' AND \"host\"::tag = '" + host + "') AND $timeFilter GROUP BY \"host\"::tag",
            alias="$tag_host")]

    #Create Panel do show CPU use Graph
    panels_list.append(CollectorTimeSeries(
        title="CPU utilization (%)",
        dataSource='default',
        targets=panels_target_list_cpu_use,
        drawStyle='line',
        lineInterpolation= COLLECTOR_LINE_INTERPOLATION,
        showPoints=COLLECTOR_SHOW_POINTS,
        gradientMode=COLLECTOR_GRADIENT_MODE,
        fillOpacity=COLLECTOR_FILL_OPACITY,
        unit="percent",
        gridPos=GridPos(h=7, w=12, x=0, y=line),
        spanNulls=COLLECTOR_SPAN_NULLS,
        legendPlacement="right",
        legendDisplayMode="table",
        legendSortBy="Name",
        legendCalcs=['mean', 'max'],
        legendSortDesc=False,
        valueMax=100,
        )
    )

    # Create Panel do show CPU Load
    panels_list.append(CollectorTimeSeries(
        title="CPU Average Load (5 min)",
        dataSource='default',
        targets=panels_target_list_cpu_load,
        drawStyle='line',
        lineInterpolation=COLLECTOR_LINE_INTERPOLATION,
        showPoints=COLLECTOR_SHOW_POINTS,
        gradientMode=COLLECTOR_GRADIENT_MODE,
        fillOpacity=COLLECTOR_FILL_OPACITY,
        unit="",
        gridPos=GridPos(h=7, w=12, x=12, y=line),
        spanNulls=COLLECTOR_SPAN_NULLS,
        legendPlacement="right",
        legendDisplayMode="table",
        legendSortBy="Name",
        legendCalcs=['mean', 'max'],
        legendSortDesc=False,
    ))

    line = line + 7

    return line, panels_list


def graph_linux_os_mem(system_name, resource_name, y_pos):
    str_title = "Memory Usage (" + resource_name + ")"
    panels_list = [RowPanel(title=str_title, gridPos=GridPos(h=1, w=24, x=0, y=y_pos))]
    pos = y_pos + 1

    target_mem = [InfluxDBTarget(
        query="SELECT  (total)-(avail) as \"Used\", (avail) as \"Available\", \"total\" as \"Total\", "
              "\"used\"/\"total\"*100 as \"Used%\" FROM \"mem\" WHERE $timeFilter AND (\"system\"::tag = '" +
              system_name + "') GROUP BY \"host\"::tag ORDER BY time DESC LIMIT 1",
        format="table")]

    json_overrides = [
        {
            "matcher": {
                "id": "byName",
                "options": "Total"
            },
            "properties": [
                {
                    "id": "custom.hideFrom",
                    "value": {
                        "tooltip": False,
                        "viz": True,
                        "legend": True
                    }
                }
            ]
        },
        {
            "matcher": {
                "id": "byName",
                "options": "Used%"
            },
            "properties": [
                {
                    "id": "unit",
                    "value": "percent"
                },
                {
                    "id": "custom.hideFrom",
                    "value": {
                        "tooltip": False,
                        "viz": True,
                        "legend": True
                    }
                }
            ]
        }
    ]

    panels_list.append(CollectorBarChart(
        title="Memory Usage",
        dataSource='default',
        targets=target_mem,
        drawStyle='line',
        lineInterpolation=COLLECTOR_LINE_INTERPOLATION,
        gradientMode=COLLECTOR_GRADIENT_MODE,
        fillOpacity=COLLECTOR_FILL_OPACITY,
        unit="decmbytes",
        gridPos=GridPos(h=7, w=24, x=0, y=pos),
        spanNulls=COLLECTOR_SPAN_NULLS,
        legendPlacement="right",
        legendDisplayMode="table",
        stacking={'mode': "normal"},
        tooltipMode="multi",
        overrides=json_overrides,
        )
    )

    pos = pos + 7

    return pos, panels_list


def graph_linux_os_fs(system_name, resource_name, metric, y_pos):
    str_title = "File System Capacity (" + resource_name + ")"
    panels_list = [RowPanel(title=str_title, gridPos=GridPos(h=1, w=24, x=0, y=y_pos))]
    pos = y_pos + 1

    for host in metric['hosts']:
        target_fs = [InfluxDBTarget(
            query="SELECT \"used\" as \"Used\", \"total\"-\"used\" as \"Available\", \"total\" as \"Total\", "
                  "\"used\"/\"total\"*100 as \"%Used\" FROM \"fs\" WHERE $timeFilter AND ( \"system\"::tag = '" +
                  system_name + "' AND \"host\"::tag = '" + host + "') GROUP BY \"mount\"::tag ORDER BY time DESC "
                                                                   "LIMIT 1",
            format="table")]

        json_overrides = [
          {
            "matcher": {
              "id": "byName",
              "options": "%Used"
            },
            "properties": [
              {
                "id": "unit",
                "value": "percent"
              },
              {
                "id": "custom.hideFrom",
                "value": {
                  "legend": True,
                  "tooltip": False,
                  "viz": True
                }
              }
            ]
          },
          {
            "matcher": {
              "id": "byName",
              "options": "Total"
            },
            "properties": [
              {
                "id": "custom.hideFrom",
                "value": {
                  "legend": True,
                  "tooltip": False,
                  "viz": True
                }
              }
            ]
          },
          {
            "matcher": {
              "id": "byName",
              "options": "Used"
            },
            "properties": [
              {
                "id": "thresholds",
                "value": {
                  "mode": "percentage",
                  "steps": [
                    {
                      "color": "green",
                      "value": None
                    },
                    {
                      "color": "red",
                      "value": 95
                    }
                  ]
                }
              },
              {
                "id": "color",
                "value": {
                  "mode": "thresholds"
                }
              }
            ]
          }
        ]

        panels_list.append(CollectorBarChart(
            title=host + " File System Capacity",
            dataSource='default',
            targets=target_fs,
            drawStyle='line',
            lineInterpolation=COLLECTOR_LINE_INTERPOLATION,
            gradientMode=COLLECTOR_GRADIENT_MODE,
            fillOpacity=COLLECTOR_FILL_OPACITY,
            unit=COLLECTOR_FS_UNITS,
            gridPos=GridPos(h=7, w=24, x=0, y=pos),
            spanNulls=COLLECTOR_SPAN_NULLS,
            legendPlacement="right",
            legendDisplayMode="table",
            stacking={"mode": "normal", "group": "A"},
            tooltipMode="multi",
            xTickLabelRotation=-45,
            valueDecimals=2,
            overrides=json_overrides,
        ))
        pos = pos + 7

    return pos, panels_list


def graph_linux_os_net(system_name, resource_name, metric, y_pos):
    str_title = "Network Usage (" + resource_name + ")"
    panels_list = [RowPanel(title=str_title, gridPos=GridPos(h=1, w=24, x=0, y=y_pos))]
    pos = y_pos + 1

    for host in metric['hosts']:
        target_net_outbound = [InfluxDBTarget(
            query="SELECT non_negative_derivative(mean(\"tx_bytes\"), 1s) FROM \"net\" WHERE (\"system\"::tag = '" +
                  system_name + "' AND \"host\"::tag = '" + host +
                  "' AND \"if\"::tag!='lo') AND $timeFilter GROUP BY time($__interval), \"if\"::tag fill(null)",
            alias="$tag_if")]

        panels_list.append(CollectorTimeSeries(
            title=host + " Network Transmit (tx)",
            dataSource='default',
            targets=target_net_outbound,
            drawStyle='line',
            lineInterpolation=COLLECTOR_LINE_INTERPOLATION,
            showPoints=COLLECTOR_SHOW_POINTS,
            gradientMode=COLLECTOR_GRADIENT_MODE,
            fillOpacity=COLLECTOR_FILL_OPACITY,
            unit=COLLECTOR_NET_UNITS,
            gridPos=GridPos(h=7, w=12, x=0, y=pos),
            spanNulls=COLLECTOR_SPAN_NULLS,
            legendPlacement="right",
            legendDisplayMode="table",
            stacking={"mode": "normal", "group": "A"},
            legendSortBy="Name",
            legendSortDesc=False,
        ))

        target_net_inbound = [InfluxDBTarget(
            query="SELECT non_negative_derivative(mean(\"rx_bytes\"), 1s) FROM \"net\" WHERE (\"system\"::tag = '" +
                  system_name + "' AND \"host\"::tag = '" + host +
                  "' AND \"if\"::tag!='lo') AND $timeFilter GROUP BY time($__interval), \"if\"::tag fill(null)",
            alias="$tag_if")]

        panels_list.append(CollectorTimeSeries(
            title=host + " Network Receive (rx)",
            dataSource='default',
            targets=target_net_inbound,
            drawStyle='line',
            lineInterpolation=COLLECTOR_LINE_INTERPOLATION,
            showPoints=COLLECTOR_SHOW_POINTS,
            gradientMode=COLLECTOR_GRADIENT_MODE,
            fillOpacity=COLLECTOR_FILL_OPACITY,
            unit=COLLECTOR_NET_UNITS,
            gridPos=GridPos(h=7, w=12, x=12, y=pos),
            spanNulls=COLLECTOR_SPAN_NULLS,
            legendPlacement="right",
            legendDisplayMode="table",
            stacking={"mode": "normal", "group": "A"},
            legendSortBy="Name",
            legendSortDesc=False,
        ))
        pos = pos + 7

    return pos, panels_list


def graph_eternus_cs8000_fs_io(system_name, resource_name, metric, y_pos):
    str_title = "File System IO (" + resource_name + ")"
    panels_list = [RowPanel(title=str_title, gridPos=GridPos(h=1, w=24, x=0, y=y_pos)), ]
    pos = y_pos + 1
    panel_width = 5
    panel_height = 14

    for host in metric['hosts']:
        panels_target_list = [InfluxDBTarget(
            query=("SELECT mean(\"svctm\") FROM \"fs_io\" WHERE (\"system\"::tag = '" + system_name +
                   "' AND \"host\"::tag = '" + host +
                   "') AND $timeFilter GROUP BY time($__interval), \"fs\"::tag, \"dm\"::tag, \"rawdev\"::tag fill(null)"),
            alias="$tag_fs $tag_dm $tag_rawdev")]

        panels_list.append(CollectorTimeSeries(
            title=host + " Service Time",
            dataSource='default',
            targets=panels_target_list,
            drawStyle='line',
            lineInterpolation=COLLECTOR_LINE_INTERPOLATION,
            showPoints=COLLECTOR_SHOW_POINTS,
            gradientMode=COLLECTOR_GRADIENT_MODE,
            fillOpacity=COLLECTOR_FILL_OPACITY,
            unit="ms",
            gridPos=GridPos(h=panel_height, w=panel_width, x=0, y=pos),
            spanNulls=COLLECTOR_SPAN_NULLS,
            legendPlacement="bottom",
            legendDisplayMode="table",
            legendCalcs=["max", "mean"],
            legendSortBy="Max",
            legendSortDesc=True,
            )
        )

        panels_target_list = [InfluxDBTarget(
            query=("SELECT mean(\"r/s\") FROM \"fs_io\" WHERE (\"system\"::tag = '" + system_name +
                   "' AND \"host\"::tag = '" + host +
                   "') AND $timeFilter GROUP BY time($__interval), \"fs\"::tag, \"dm\"::tag, \"rawdev\"::tag fill(null)"),
            alias="$tag_fs $tag_dm $tag_rawdev")]

        panels_list.append(CollectorTimeSeries(
            title=host + " Reads/s",
            dataSource='default',
            targets=panels_target_list,
            drawStyle='line',
            lineInterpolation=COLLECTOR_LINE_INTERPOLATION,
            showPoints=COLLECTOR_SHOW_POINTS,
            gradientMode=COLLECTOR_GRADIENT_MODE,
            fillOpacity=COLLECTOR_FILL_OPACITY,
            unit="iops",
            gridPos=GridPos(h=panel_height, w=panel_width, x=1 * panel_width, y=pos),
            spanNulls=COLLECTOR_SPAN_NULLS,
            legendPlacement="bottom",
            legendDisplayMode="table",
            legendCalcs=["max", "mean"],
            legendSortBy="Max",
            legendSortDesc=True,
            )
        )

        panels_target_list = [InfluxDBTarget(
            query=("SELECT mean(\"r_await\") FROM \"fs_io\" WHERE (\"system\"::tag = '" + system_name +
                   "' AND \"host\"::tag = '" + host +
                   "') AND $timeFilter GROUP BY time($__interval), \"fs\"::tag, \"dm\"::tag, \"rawdev\"::tag fill(null)"),
            alias="$tag_fs $tag_dm $tag_rawdev")]

        panels_list.append(CollectorTimeSeries(
            title=host + " Read Average Wait Time",
            dataSource='default',
            targets=panels_target_list,
            drawStyle='line',
            lineInterpolation=COLLECTOR_LINE_INTERPOLATION,
            showPoints=COLLECTOR_SHOW_POINTS,
            gradientMode=COLLECTOR_GRADIENT_MODE,
            fillOpacity=COLLECTOR_FILL_OPACITY,
            unit="ms",
            gridPos=GridPos(h=panel_height, w=panel_width, x=2 * panel_width, y=pos),
            spanNulls=COLLECTOR_SPAN_NULLS,
            legendPlacement="bottom",
            legendDisplayMode="table",
            legendCalcs=["max", "mean"],
            legendSortBy="Max",
            legendSortDesc=True,
            )
        )

        panels_target_list = [InfluxDBTarget(
            query=("SELECT mean(\"w/s\") FROM \"fs_io\" WHERE (\"system\"::tag = '" + system_name +
                   "' AND \"host\"::tag = '" + host +
                   "') AND $timeFilter GROUP BY time($__interval), \"fs\"::tag, \"dm\"::tag, \"rawdev\"::tag fill(null)"),
            alias="$tag_fs $tag_dm $tag_rawdev")]

        panels_list.append(CollectorTimeSeries(
            title=host + " Writes/s",
            dataSource='default',
            targets=panels_target_list,
            drawStyle='line',
            lineInterpolation=COLLECTOR_LINE_INTERPOLATION,
            showPoints=COLLECTOR_SHOW_POINTS,
            gradientMode=COLLECTOR_GRADIENT_MODE,
            fillOpacity=COLLECTOR_FILL_OPACITY,
            unit="iops",
            gridPos=GridPos(h=panel_height, w=panel_width, x=3 * panel_width, y=pos),
            spanNulls=COLLECTOR_SPAN_NULLS,
            legendPlacement="bottom",
            legendDisplayMode="table",
            legendCalcs=["max", "mean"],
            legendSortBy="Max",
            legendSortDesc=True,
            )
        )

        panels_target_list = [InfluxDBTarget(
            query=("SELECT mean(\"w_await\") FROM \"fs_io\" WHERE (\"system\"::tag = '" + system_name +
                   "' AND \"host\"::tag = '" + host +
                   "') AND $timeFilter GROUP BY time($__interval), \"fs\"::tag, \"dm\"::tag, \"rawdev\"::tag fill(null)"),
            alias="$tag_fs $tag_dm $tag_rawdev")]

        panels_list.append(CollectorTimeSeries(
            title=host + " Write Average Wait Time",
            dataSource='default',
            targets=panels_target_list,
            drawStyle='line',
            lineInterpolation=COLLECTOR_LINE_INTERPOLATION,
            showPoints=COLLECTOR_SHOW_POINTS,
            gradientMode=COLLECTOR_GRADIENT_MODE,
            fillOpacity=COLLECTOR_FILL_OPACITY,
            unit="ms",
            gridPos=GridPos(h=panel_height, w=panel_width - 1, x=4 * panel_width, y=pos),
            spanNulls=COLLECTOR_SPAN_NULLS,
            legendPlacement="bottom",
            legendDisplayMode="table",
            legendCalcs=["max", "mean"],
            legendSortBy="Max",
            legendSortDesc=True,
            )
        )

        pos = pos + 7

    return pos, panels_list


def graph_eternus_cs8000_drives(system_name, resource_name, y_pos):
    str_title = "Tape Libraries (" + resource_name + ")"
    panels_list = [RowPanel(title=str_title, gridPos=GridPos(h=1, w=24, x=0, y=y_pos))]
    line = y_pos + 1

    target_list = [InfluxDBTarget(
        query="SELECT \"total\" as Total , \"used\"+\"other\" as Used, \"other\" as Unavailable FROM \"drives\" WHERE (\"system\"::tag = '" +
              system_name + "' AND \"tapename\"::tag =~ /^$tapename$/) AND $timeFilter",
        )
    ]

    override_lst = [
      {
        "matcher": {
          "id": "byName",
          "options": "drives.Unavailable"
        },
        "properties": [
          {
            "id": "custom.fillOpacity",
            "value": 100
          },
          {
            "id": "custom.gradientMode",
            "value": "none"
          },
          {
            "id": "color",
            "value": {
              "fixedColor": "#ff331c",
              "mode": "fixed"
            }
          }
        ]
      },
      {
        "matcher": {
          "id": "byName",
          "options": "drives.Total"
        },
        "properties": [
          {
            "id": "color",
            "value": {
              "mode": "fixed",
              "fixedColor": "blue"
            }
          }
        ]
      },
      {
        "matcher": {
          "id": "byName",
          "options": "drives.Used"
        },
        "properties": [
          {
            "id": "color",
            "value": {
              "mode": "fixed",
              "fixedColor": "green"
            }
          }
        ]
      }
    ]

    panels_list.append(CollectorTimeSeries(
        title="Tape Library $tapename",
        repeat=Repeat(direction='h', variable='tapename', maxPerRow=6),
        dataSource='default',
        targets=target_list,
        drawStyle='line',
        lineInterpolation='stepAfter',
        showPoints='auto',
        gradientMode='none',
        fillOpacity=50,
        unit='',
        gridPos=GridPos(h=7, w=12, x=0, y=line),
        spanNulls=COLLECTOR_SPAN_NULLS,
        legendPlacement='right',
        legendDisplayMode='table',
        valueDecimals=0,
        overrides=override_lst,
    )
    )

    line = line + 7

    return line, panels_list


def graph_eternus_cs8000_medias(system_name, resource_name, y_pos):
    str_title = "Tape Medias (" + resource_name + ")"
    panels_list = [RowPanel(title=str_title, gridPos=GridPos(h=1, w=24, x=0, y=y_pos))]
    line = y_pos + 1

    target_list = [InfluxDBTarget(
        query="SELECT  \"Total Cap GiB\" as \"Total Capacity\", \"Total Clean Medias\", \"Total Fault\","
              " \"Total Ina\" as \"Total Inactive\", \"Total Medias\", \"Total Val GiB\" as \"Total Valid\", "
              "\"Val %\" as \"Valid %\"  FROM \"medias\" WHERE $timeFilter AND (\"system\"::tag='" + system_name +
              "') GROUP BY \"host\"::tag, \"tapename\"::tag ORDER BY DESC LIMIT 1",
        format="table")]

    override_lst = [
      {
        "matcher": {
          "id": "byName",
          "options": "Time"
        },
        "properties": [
          {
            "id": "custom.hidden",
            "value": True
          }
        ]
      },
      {
        "matcher": {
          "id": "byName",
          "options": "Total Capacity"
        },
        "properties": [
          {
            "id": "unit",
            "value": "decgbytes"
          }
        ]
      },
      {
        "matcher": {
          "id": "byName",
          "options": "Total Valid"
        },
        "properties": [
          {
            "id": "unit",
            "value": "decgbytes"
          }
        ]
      },
      {
        "matcher": {
          "id": "byName",
          "options": "Valid %"
        },
        "properties": [
          {
            "id": "unit",
            "value": "percent"
          },
          {
            "id": "thresholds",
            "value": {
              "mode": "absolute",
              "steps": [
                {
                  "color": "green",
                  "value": None
                },
                {
                  "color": "#EAB839",
                  "value": 65
                },
                {
                  "color": "red",
                  "value": 75
                }
              ]
            }
          }
        ]
      }
    ]

    thres = [
        {
            "color": "text",
            "value": None
        }
    ]

    panels_list.append(CollectorTable(
        title="Tape Medias",
        dataSource='default',
        targets=target_list,
        gridPos=GridPos(h=7, w=24, x=0, y=line),
        filterable=True,
        displayMode="color-text",
        colorMode="thresholds",
        overrides=override_lst,
        thresholds=thres,
        )
    )

    line = line + 7

    return line, panels_list


def graph_eternus_cs8000_pvgprofile(system_name, resource_name, y_pos):
    str_title = "Physical Volume Group Profile (" + resource_name + ")"
    panels_list = [RowPanel(title=str_title, gridPos=GridPos(h=1, w=24, x=0, y=y_pos))]
    line = y_pos + 1

    target_list = [InfluxDBTarget(
        query="SELECT \"Total Medias\", \"Fault\", \"Ina\", \"Scr\", \"-10\", \"-20\", \"-30\", \"-40\", \"-50\", \"-60\", \"-70\", \"-80\", \"-90\", \">90\", \"Total Cap (GiB)\", \"Total Used (GiB)\" from pvgprofile WHERE $timeFilter AND (\"system\"::tag='" + system_name + "') GROUP BY \"pvgname\"::tag, \"host\"::tag ORDER BY DESC LIMIT 1",
        format="table")]

    override_lst = [
        {
            "matcher": {
                "id": "byName",
                "options": "Time"
            },
            "properties": [
                {
                    "id": "custom.hidden",
                    "value": True
                }
            ]
        },
        {
            "matcher": {
                "id": "byName",
                "options": "Scr"
            },
            "properties": [
                {
                    "id": "thresholds",
                    "value": {
                        "mode": "absolute",
                        "steps": [
                            {
                                "color": "green",
                                "value": None
                            },
                            {
                                "color": "red",
                                "value": 0
                            },
                            {
                                "color": "#EAB839",
                                "value": 10
                            },
                            {
                                "color": "green",
                                "value": 15
                            }
                        ]
                    }
                }
            ]
        },
        {
            "matcher": {
                "id": "byName",
                "options": "Total Cap (GiB)"
            },
            "properties": [
                {
                    "id": "unit",
                    "value": "decgbytes"
                }
            ]
        },
        {
            "matcher": {
                "id": "byName",
                "options": "Total Used (GiB)"
            },
            "properties": [
                {
                    "id": "unit",
                    "value": "decgbytes"
                }
            ]
        }
    ]

    thres = [
        {
            "color": "text",
            "value": None
        }
    ]

    panels_list.append(CollectorTable(
        title="Physical Volume Group",
        dataSource='default',
        targets=target_list,
        gridPos=GridPos(h=7, w=24, x=0, y=line),
        filterable=True,
        displayMode="color-text",
        colorMode="thresholds",
        overrides=override_lst,
        # thresholds=Threshold(line=False,color='text', index=0, value=0.0, op=EVAL_GT),
        thresholds=thres,
        fontSize="85%",
        minWidth = 55,
        align="center",
    ))

    line = line + 7

    return line, panels_list


def graph_eternus_cs8000_fc(system_name, resource_name, metric, y_pos):
    str_title = "FibreChannel Usage (" + resource_name + ")"
    panels_list = [RowPanel(title=str_title, gridPos=GridPos(h=1, w=24, x=0, y=y_pos))]
    pos = y_pos + 1

    for host in metric['hosts']:
        target_net_outbound = [InfluxDBTarget(
            query="SELECT non_negative_derivative(mean(\"tx_bytes\"), 1s) FROM \"fc\" WHERE (\"system\"::tag = '" + system_name + "' AND \"host\"::tag = '" + host + "') AND $timeFilter GROUP BY time($__interval), \"hba\"::tag fill(null)",
            alias="$tag_hba")]

        panels_list.append(CollectorTimeSeries(
            title=host + " FC Transmit (tx)",
            dataSource='default',
            targets=target_net_outbound,
            drawStyle='line',
            lineInterpolation=COLLECTOR_LINE_INTERPOLATION,
            showPoints=COLLECTOR_SHOW_POINTS,
            gradientMode=COLLECTOR_GRADIENT_MODE,
            fillOpacity=COLLECTOR_FILL_OPACITY,
            unit=COLLECTOR_FC_UNITS,
            gridPos=GridPos(h=7, w=12, x=0, y=pos),
            spanNulls=COLLECTOR_SPAN_NULLS,
            legendPlacement="right",
            legendDisplayMode="table",
            stacking={"mode": "normal", "group": "A"},
            legendSortBy="Name",
            legendSortDesc=False,
        ))

        target_net_inbound = [InfluxDBTarget(
            query="SELECT non_negative_derivative(mean(\"rx_bytes\"), 1s) FROM \"fc\" WHERE (\"system\"::tag = '" + system_name + "' AND \"host\"::tag = '" + host + "') AND $timeFilter GROUP BY time($__interval), \"hba\"::tag fill(null)",
            alias="$tag_hba")]

        panels_list.append(CollectorTimeSeries(
            title=host + " FC Receive (rx)",
            dataSource='default',
            targets=target_net_inbound,
            drawStyle='line',
            lineInterpolation=COLLECTOR_LINE_INTERPOLATION,
            showPoints=COLLECTOR_SHOW_POINTS,
            gradientMode=COLLECTOR_GRADIENT_MODE,
            fillOpacity=COLLECTOR_FILL_OPACITY,
            unit=COLLECTOR_FC_UNITS,
            gridPos=GridPos(h=7, w=12, x=12, y=pos),
            spanNulls=COLLECTOR_SPAN_NULLS,
            legendPlacement="right",
            legendDisplayMode="table",
            stacking={"mode": "normal", "group": "A"},
            legendSortBy="Name",
            legendSortDesc=False,
        ))
        pos = pos + 7

    return pos, panels_list

