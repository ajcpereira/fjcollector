#################################################################################
#                                                                               #
#                       IDENTIFICATION DIVISION                                 #
#                                                                               #
#################################################################################
# Module: GrafanaLib class extensions (grafanalib_ext.py)
#
# This module extends some of the grafanalib classes, that will be used in the
# collector dashboards.
#       CollectorTimeSeries (extended properties)
#       CollectorBarChart   (doesn't exist in grafanalib release)
#       CollectorTable      (extended properties)
#


#################################################################################
#                                                                               #
#                       ENVIRONMENT DIVISION                                    #
#                                                                               #
#################################################################################

from grafanalib.core import *
from grafanalib.influxdb import *


#################################################################################
#                                                                               #
#                       DATA DIVISION                                           #
#                                                                               #
#################################################################################

BARCHART_TYPE = 'barchart'

# Common graphics visualization properties, to enable a consistent view
COLLECTOR_GRADIENT_MODE = 'none' #none, opacity, hue
COLLECTOR_SHOW_POINTS = 'never'
COLLECTOR_LINE_INTERPOLATION = 'smooth'
COLLECTOR_FILL_OPACITY = 25
COLLECTOR_SPAN_NULLS = True # True
COLLECTOR_FC_UNITS = 'MBs' # Data rate MBytes/sec = 'MBs'
COLLECTOR_NET_UNITS = 'binBps' # Data rate/ Bytes/sec = 'Bps' or Data rate/ Bytes/sec(IEC)
COLLECTOR_FS_UNITS = 'kbytes' # kibibytes
COLLECTOR_MEM_UNITS = 'decmbytes'

#################################################################################
#                                                                               #
#                       FUNCTION  DIVISION                                      #
#                                                                               #
#################################################################################

########################################################################################################################
#
# Class: CollectorBarChart
#
# Grafanalib doesn't have a class to manipulate BarChart
# this is a new class, based on TimeSeries class, to create BarChart graphs
########################################################################################################################

@attr.s
class CollectorBarChart(Panel):
    """Generates Time Series panel json structure added in Grafana v8

    Grafana doc on time series: https://grafana.com/docs/grafana/latest/panels/visualizations/time-series/

    :param axisPlacement: auto(Default), left. right, hidden
    :param axisLabel: axis label string
    :param barAlignment: bar alignment
        -1 (left), 0 (centre, default), 1
    :param colorMode: Color mode
        palette-classic (Default),
    :param drawStyle: how to display your time series data
        line (Default), bars, points
    :param fillOpacity: fillOpacity
    :param gradientMode: gradientMode
    :param legendDisplayMode: refine how the legend appears in your visualization
        list (Default), table, hidden
    :param legendPlacement: bottom (Default), right
    :param legendCalcs: which calculations should be displayed in the legend. Defaults to an empty list.
        Possible values are: allIsNull, allIsZero, changeCount, count, delta, diff, diffperc,
        distinctCount, firstNotNull, max, mean, min, logmin, range, step, total. For more information see
    :param lineInterpolation: line interpolation
        linear (Default), smooth, stepBefore, stepAfter
    :param lineWidth: line width, default 1
    :param mappings: To assign colors to boolean or string values, use Value mappings
    :param overrides: To override the base characteristics of certain timeseries data
    :param pointSize: point size, default 5
    :param scaleDistributionType: axis scale linear or log
    :param scaleDistributionLog: Base of if logarithmic scale type set, default 2
    :param spanNulls: connect null values, default False
    :param showPoints: show points
        auto (Default), always, never
    :param stacking: dict to enable stacking, {"mode": "normal", "group": "A"}
    :param thresholds: single stat thresholds
    :param tooltipMode: When you hover your cursor over the visualization, Grafana can display tooltips
        single (Default), multi, none
    :param tooltipSort: To sort the tooltips
        none (Default), asc, desc
    :param unit: units
    :param thresholdsStyleMode: thresholds style mode off (Default), area, line, line+area
    :param valueMin: Minimum value for Panel
    :param valueMax: Maximum value for Panel
    :param valueDecimals: Number of display decimals
    :param axisSoftMin: soft minimum Y axis value
    :param axisSoftMax: soft maximum Y axis value
    """

    axisPlacement = attr.ib(default='auto', validator=instance_of(str))
    axisLabel = attr.ib(default='', validator=instance_of(str))
    barAlignment = attr.ib(default=0, validator=instance_of(int))
    colorMode = attr.ib(default='palette-classic', validator=instance_of(str))
    drawStyle = attr.ib(default='line', validator=instance_of(str))
    fillOpacity = attr.ib(default=0, validator=instance_of(int))
    gradientMode = attr.ib(default='none', validator=instance_of(str))
    legendDisplayMode = attr.ib(default='list', validator=instance_of(str))
    legendPlacement = attr.ib(default='bottom', validator=instance_of(str))
    legendCalcs = attr.ib(
        factory=list,
        validator=attr.validators.deep_iterable(
            member_validator=in_([
                'lastNotNull',
                'min',
                'mean',
                'max',
                'last',
                'firstNotNull',
                'first',
                'sum',
                'count',
                'range',
                'delta',
                'step',
                'diff',
                'logmin',
                'allIsZero',
                'allIsNull',
                'changeCount',
                'distinctCount',
                'diffperc',
                'allValues'
            ]),
            iterable_validator=instance_of(list),
        ),
    )
    lineInterpolation = attr.ib(default='linear', validator=instance_of(str))
    lineWidth = attr.ib(default=1, validator=instance_of(int))
    mappings = attr.ib(default=attr.Factory(list))
    overrides = attr.ib(default=attr.Factory(list))
    pointSize = attr.ib(default=5, validator=instance_of(int))
    scaleDistributionType = attr.ib(default='linear', validator=instance_of(str))
    scaleDistributionLog = attr.ib(default=2, validator=instance_of(int))
    spanNulls = attr.ib(default=False, validator=instance_of(bool))
    showPoints = attr.ib(default='auto', validator=instance_of(str))
    stacking = attr.ib(factory=dict, validator=instance_of(dict))
    tooltipMode = attr.ib(default='single', validator=instance_of(str))
    tooltipSort = attr.ib(default='none', validator=instance_of(str))
    unit = attr.ib(default='', validator=instance_of(str))
    thresholdsStyleMode = attr.ib(default='off', validator=instance_of(str))

    valueMin = attr.ib(default=None, validator=attr.validators.optional(instance_of(int)))
    valueMax = attr.ib(default=None, validator=attr.validators.optional(instance_of(int)))
    valueDecimals = attr.ib(default=None, validator=attr.validators.optional(instance_of(int)))
    axisSoftMin = attr.ib(default=None, validator=attr.validators.optional(instance_of(int)))
    axisSoftMax = attr.ib(default=None, validator=attr.validators.optional(instance_of(int)))

    # added by MachadoN / BEGIN
    xTickLabelRotation = attr.ib(default=0, validator=instance_of(int))

    legendSortBy = attr.ib(default='max', validator=instance_of(str))
    legendSortDesc = attr.ib(default=False, validator=instance_of(bool))

    # added by MachadoN / END

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
                            # 'stacking': self.stacking,
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
                            'axisSoftMin': self.axisSoftMin,
                            'axisSoftMax': self.axisSoftMax
                        },
                        'mappings': self.mappings,
                        "min": self.valueMin,
                        "max": self.valueMax,
                        "decimals": self.valueDecimals,
                        'unit': self.unit
                    },
                    'overrides': self.overrides
                },
                'options': {
                    'xTickLabelRotation': self.xTickLabelRotation,
                    "stacking": self.stacking,
                    'legend': {
                        'displayMode': self.legendDisplayMode,
                        'placement': self.legendPlacement,
                        'calcs': self.legendCalcs,
                        'sortBy': self.legendSortBy,
                        'sortDesc': self.legendSortDesc
                    },
                    'tooltip': {
                        'mode': self.tooltipMode,
                        'sort': self.tooltipSort
                    }
                },
                'type': BARCHART_TYPE,
            }
        )


########################################################################################################################
#
# Class: CollectorTimeSeries
#
# Created a new class based on code from core.py of grafanalib project, with some extended properties.
#
#######################################################################################################################

@attr.s
class CollectorTimeSeries(Panel):
    """Generates Time Series panel json structure added in Grafana v8

    Grafana doc on time series: https://grafana.com/docs/grafana/latest/panels/visualizations/time-series/

    :param axisPlacement: auto(Default), left. right, hidden
    :param axisLabel: axis label string
    :param barAlignment: bar alignment
        -1 (left), 0 (centre, default), 1
    :param colorMode: Color mode
        palette-classic (Default),
    :param drawStyle: how to display your time series data
        line (Default), bars, points
    :param fillOpacity: fillOpacity
    :param gradientMode: gradientMode
    :param legendDisplayMode: refine how the legend appears in your visualization
        list (Default), table, hidden
    :param legendPlacement: bottom (Default), right
    :param legendCalcs: which calculations should be displayed in the legend. Defaults to an empty list.
        Possible values are: allIsNull, allIsZero, changeCount, count, delta, diff, diffperc,
        distinctCount, firstNotNull, max, mean, min, logmin, range, step, total. For more information see
    :param lineInterpolation: line interpolation
        linear (Default), smooth, stepBefore, stepAfter
    :param lineWidth: line width, default 1
    :param mappings: To assign colors to boolean or string values, use Value mappings
    :param overrides: To override the base characteristics of certain timeseries data
    :param pointSize: point size, default 5
    :param scaleDistributionType: axis scale linear or log
    :param scaleDistributionLog: Base of if logarithmic scale type set, default 2
    :param spanNulls: connect null values, default False
    :param showPoints: show points
        auto (Default), always, never
    :param stacking: dict to enable stacking, {"mode": "normal", "group": "A"}
    :param thresholds: single stat thresholds
    :param tooltipMode: When you hover your cursor over the visualization, Grafana can display tooltips
        single (Default), multi, none
    :param tooltipSort: To sort the tooltips
        none (Default), asc, desc
    :param unit: units
    :param thresholdsStyleMode: thresholds style mode off (Default), area, line, line+area
    :param valueMin: Minimum value for Panel
    :param valueMax: Maximum value for Panel
    :param valueDecimals: Number of display decimals
    :param axisSoftMin: soft minimum Y axis value
    :param axisSoftMax: soft maximum Y axis value
    """

    axisPlacement = attr.ib(default='auto', validator=instance_of(str))
    axisLabel = attr.ib(default='', validator=instance_of(str))
    barAlignment = attr.ib(default=0, validator=instance_of(int))
    colorMode = attr.ib(default='palette-classic', validator=instance_of(str))
    drawStyle = attr.ib(default='line', validator=instance_of(str))
    fillOpacity = attr.ib(default=0, validator=instance_of(int))
    gradientMode = attr.ib(default='none', validator=instance_of(str))
    legendDisplayMode = attr.ib(default='list', validator=instance_of(str))
    legendPlacement = attr.ib(default='bottom', validator=instance_of(str))
    legendCalcs = attr.ib(
        factory=list,
        validator=attr.validators.deep_iterable(
            member_validator=in_([
                'lastNotNull',
                'min',
                'mean',
                'max',
                'last',
                'firstNotNull',
                'first',
                'sum',
                'count',
                'range',
                'delta',
                'step',
                'diff',
                'logmin',
                'allIsZero',
                'allIsNull',
                'changeCount',
                'distinctCount',
                'diffperc',
                'allValues'
            ]),
            iterable_validator=instance_of(list),
        ),
    )
    lineInterpolation = attr.ib(default='linear', validator=instance_of(str))
    lineWidth = attr.ib(default=1, validator=instance_of(int))
    mappings = attr.ib(default=attr.Factory(list))
    overrides = attr.ib(default=attr.Factory(list))
    pointSize = attr.ib(default=5, validator=instance_of(int))
    scaleDistributionType = attr.ib(default='linear', validator=instance_of(str))
    scaleDistributionLog = attr.ib(default=2, validator=instance_of(int))
    spanNulls = attr.ib(default=False, validator=instance_of(bool))
    showPoints = attr.ib(default='auto', validator=instance_of(str))
    stacking = attr.ib(factory=dict, validator=instance_of(dict))
    tooltipMode = attr.ib(default='single', validator=instance_of(str))
    tooltipSort = attr.ib(default='none', validator=instance_of(str))
    unit = attr.ib(default='', validator=instance_of(str))
    thresholdsStyleMode = attr.ib(default='off', validator=instance_of(str))

    valueMin = attr.ib(default=None, validator=attr.validators.optional(instance_of(int)))
    valueMax = attr.ib(default=None, validator=attr.validators.optional(instance_of(int)))
    valueDecimals = attr.ib(default=None, validator=attr.validators.optional(instance_of(int)))
    axisSoftMin = attr.ib(default=None, validator=attr.validators.optional(instance_of(int)))
    axisSoftMax = attr.ib(default=None, validator=attr.validators.optional(instance_of(int)))

    # added by MachadoN / BEGIN
    legendSortBy = attr.ib(default='max', validator=instance_of(str))
    legendSortDesc = attr.ib(default=False, validator=instance_of(bool))

    # added by MachadoN / END

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
                            'stacking': self.stacking,
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
                            'axisSoftMin': self.axisSoftMin,
                            'axisSoftMax': self.axisSoftMax
                        },
                        'mappings': self.mappings,
                        "min": self.valueMin,
                        "max": self.valueMax,
                        "decimals": self.valueDecimals,
                        'unit': self.unit
                    },
                    'overrides': self.overrides
                },
                'options': {
                    'legend': {
                        'displayMode': self.legendDisplayMode,
                        'placement': self.legendPlacement,
                        'calcs': self.legendCalcs,
                        'sortBy': self.legendSortBy,
                        'sortDesc': self.legendSortDesc
                    },
                    'tooltip': {
                        'mode': self.tooltipMode,
                        'sort': self.tooltipSort
                    }
                },
                'type': TIMESERIES_TYPE,
            }
        )


########################################################################################################################
#
# Class: CollectorTable
#
# Created a new class based on code from core.py of grafanalib project, with some extended properties.
#
#######################################################################################################################
@attr.s
class CollectorTable(Panel):
    """Generates Table panel json structure

    Now supports Grafana v8+
    Grafana doc on table: https://grafana.com/docs/grafana/latest/visualizations/table/

    :param align: Align cell contents; auto (default), left, center, right
    :param colorMode: Default thresholds
    :param columns: Table columns for Aggregations view
    :param displayMode: By default, Grafana automatically chooses display settings, you can choose;
        color-text, color-background, color-background-solid, gradient-gauge, lcd-gauge, basic, json-view
    :param fontSize: Defines value font size
    :param filterable: Allow user to filter columns, default False
    :param mappings: To assign colors to boolean or string values, use Value mappings
    :param overrides: To override the base characteristics of certain data
    :param showHeader: Show the table header
    :param unit: units
    :param sortBy: Sort rows by table fields
    """

    align = attr.ib(default='auto', validator=instance_of(str))
    colorMode = attr.ib(default='thresholds', validator=instance_of(str))
    columns = attr.ib(default=attr.Factory(list))
    displayMode = attr.ib(default='auto', validator=instance_of(str))
    fontSize = attr.ib(default='100%')
    filterable = attr.ib(default=False, validator=instance_of(bool))
    mappings = attr.ib(default=attr.Factory(list))
    overrides = attr.ib(default=attr.Factory(list))
    showHeader = attr.ib(default=True, validator=instance_of(bool))
    span = attr.ib(default=6),
    unit = attr.ib(default='', validator=instance_of(str))
    sortBy = attr.ib(default=attr.Factory(list), validator=attr.validators.deep_iterable(
        member_validator=instance_of(TableSortByField),
        iterable_validator=instance_of(list)
    ))

    # added by MachadoN / BEGIN
    minWidth = attr.ib(default=150, validator=instance_of(int))
    # added by MachadoN / END

    @classmethod
    def with_styled_columns(cls, columns, styles=None, **kwargs):
        """Styled columns is not support in Grafana v8 Table"""
        print("Error: Styled columns is not support in Grafana v8 Table")
        print("Please see https://grafana.com/docs/grafana/latest/visualizations/table/ for more options")
        raise NotImplementedError


    def to_json_data(self):
        return self.panel_json(
            {
                "color": {
                    "mode": self.colorMode
                },
                'columns': self.columns,
                'fontSize': self.fontSize,
                'fieldConfig': {
                    'defaults': {
                        'custom': {
                            'align': self.align,
                            'displayMode': self.displayMode,
                            'filterable': self.filterable,
                            # added by MachadoN / BEGIN
                            'minWidth': self.minWidth
                            # added by MachadoN / END
                        },
                        'unit': self.unit
                    },
                    'overrides': self.overrides
                },
                'hideTimeOverride': self.hideTimeOverride,
                'mappings': self.mappings,
                'minSpan': self.minSpan,
                'options': {
                    'showHeader': self.showHeader,
                    'sortBy': self.sortBy
                },
                'type': TABLE_TYPE,
            }
        )


@attr.s
class CollectorPieChartv2(Panel):
    """Generates Pie Chart panel json structure
    Grafana docs on Pie Chart: https://grafana.com/docs/grafana/latest/visualizations/pie-chart-panel/

    :param custom: Custom overides
    :param colorMode: Color mode
        palette-classic (Default),
    :param legendDisplayMode: Display mode of legend: list, table or hidden
    :param legendPlacement: Location of the legend in the panel: bottom or right
    :param legendValues: List of value to be shown in legend eg. ['value', 'percent']
    :param mappings: To assign colors to boolean or string values, use Value mappings
    :param overrides: Overrides
    :param pieType: Pie chart type
        pie (Default), donut
    :param reduceOptionsCalcs: Reducer function / calculation
    :param reduceOptionsFields: Fields that should be included in the panel
    :param reduceOptionsValues: Calculate a single value per column or series or show each row
    :param tooltipMode: Tooltip mode
        single (Default), multi, none
    :param unit: units
    """

    custom = attr.ib(factory=dict, validator=instance_of(dict))
    colorMode = attr.ib(default='palette-classic', validator=instance_of(str))
    legendDisplayMode = attr.ib(default='list', validator=instance_of(str))
    legendPlacement = attr.ib(default='bottom', validator=instance_of(str))
    legendValues = attr.ib(factory=list, validator=instance_of(list))
    mappings = attr.ib(default=attr.Factory(list))
    overrides = attr.ib(factory=list, validator=instance_of(list))
    pieType = attr.ib(default='pie', validator=instance_of(str))
    reduceOptionsCalcs = attr.ib(default=['lastNotNull'], validator=instance_of(list))
    reduceOptionsFields = attr.ib(default='', validator=instance_of(str))
    reduceOptionsValues = attr.ib(default=False, validator=instance_of(bool))
    tooltipMode = attr.ib(default='single', validator=instance_of(str))
    unit = attr.ib(default='', validator=instance_of(str))

    # added by MachadoN / BEGIN
    displayLabels = attr.ib(factory=list, validator=instance_of(list))
    # added by MachadoN / END

    def to_json_data(self):
        return self.panel_json(
            {
                'fieldConfig': {
                    'defaults': {
                        'color': {
                            'mode': self.colorMode
                        },
                        'custom': self.custom,
                        'mappings': self.mappings,
                        'unit': self.unit,
                    },
                    'overrides': self.overrides,
                },
                'options': {
                    'reduceOptions': {
                        'values': self.reduceOptionsValues,
                        'calcs': self.reduceOptionsCalcs,
                        'fields': self.reduceOptionsFields
                    },
                    'pieType': self.pieType,
                    'tooltip': {
                        'mode': self.tooltipMode
                    },
                    'legend': {
                        'displayMode': self.legendDisplayMode,
                        'placement': self.legendPlacement,
                        'values': self.legendValues
                    },
                    # added by MachadoN / BEGIN
                    'displayLabels': self.displayLabels,
                    # added by MachadoN / END
                },
                'type': PIE_CHART_V2_TYPE,
            }
        )
