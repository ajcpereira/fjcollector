#################################################################################
#                                                                               #
#                       ENVIRONMENT DIVISION                                    #
#                                                                               #
#################################################################################
import yaml
from typing import List, Literal, Optional
from pydantic import BaseModel, StrictStr, PositiveInt, Field
from pydantic.networks import IPvAnyAddress
import os
import logging
import sys

#################################################################################
#                                                                               #
#                       DATA DIVISION                                           #
#                                                                               #
#################################################################################


#################################################################################
#                                                                               #
#                       PROCEDURE DIVISION                                      #
#                                                                               #
#################################################################################

########## FUNCTION GET AND CHECK CONFIG FILE  ##################################
def configfile_read(cmd_parameters, configfile_default):
    if len(cmd_parameters) == 1:
        try:
            if os.path.isfile(configfile_default):
                    logging.info("Using default configfile config/config.yaml")
                    config = read_yaml(configfile_default)
                    orig_mtime=(os.path.getmtime(configfile_default))
                    configfile_running=configfile_default
        except Exception as msgerr:
            logging.error("Can't handle configfile - %s - with error - %s" % (configfile_default,msgerr))
            sys.exit()            
    elif len(cmd_parameters) == 2:
        try:
            if os.path.isfile(cmd_parameters[1]):
                config = read_yaml(cmd_parameters[1])
                orig_mtime=(os.path.getmtime(cmd_parameters[1]))
                configfile_running=cmd_parameters[1]
            else:
                logging.error('No valid configfile - %s' % cmd_parameters[1])
                sys.exit()
        except Exception as msgerr:
            logging.error("Can't handle configfile - %s - with error - %s" % (cmd_parameters[1],msgerr))
            sys.exit()        
    elif len(cmd_parameters) > 2: 
        logging.error("Only configfile path is needed")
        sys.exit()

    return config, orig_mtime, configfile_running
########## FUNCTION GET AND CHECK CONFIG FILE  ##################################

########## CLASS VALIDATES MIXING OF RESOURCE TYPES AND METRICS FROM YAML #######
class AllowedMetrics:
    allowed_metrics = {
        'eternus_icp': [['fs', 'tgt'], ['cs_iostat', 'cs_iostat']],
        'linux_os': [['cpu', 'mem', 'disk', 'fs'], ['cs_iostat', 'cs_iostat', 'cs_iostat', 'cs_iostat']],
        'windows_os': [['wcpu', 'wmem', 'wdisk'], ['cs_iostat', 'cs_iostat', 'cs_iostat']],
        'fj_ism': [['temp'], ['ism_temp']]
    }

    @classmethod
    def get_func_name(self, resource_type, metric_name):
    
        metrics_list = self.allowed_metrics.get(resource_type)
        
        try:
            if metric_name in metrics_list[0]:
                index = metrics_list[0].index(metric_name)
        except TypeError:
            print("Selected resource_type - %s - is not allowed, values can be one of the following keys - %s" % (resource_type, self.allowed_metrics.keys()))
            exit()            

        if metric_name in metrics_list[0]:
            index = metrics_list[0].index(metric_name)
            return metrics_list[1][index]
        else:
            print("Selected metric - %s - is not allowed for this resource_type - %s - allowed values are - %s" % (metric_name, resource_type, metrics_list[0]))
            exit()
########## CLASS VALIDATES MIXING OF RESOURCE TYPES AND METRICS FROM YAML #######

########## CLASS FROM PYDANTIC TO VALIDATE YAML SCHEMA ##########################
class Ip(BaseModel):
    ip: IPvAnyAddress
    alias: Optional[StrictStr] = None
    ip_snmp_community: Optional[StrictStr] = None
    ip_use_sudo: Optional[bool] = None
    ip_host_keys: Optional[str] = Field(None, max_length=100)
    ip_bastion: Optional[IPvAnyAddress] = Field(None)

class Parameters(BaseModel):
    user: StrictStr
    host_keys: Optional[str] = Field(None, max_length=100)
    poll: PositiveInt = Field(..., ge=1, le=1440)
    use_sudo: Optional[bool] = None
    snmp_community:Optional[str] = Field(None, max_length=100)
    bastion: Optional[IPvAnyAddress] = Field(None)
    ism_password: Optional[str] = Field(None)
    ism_port: Optional[PositiveInt] = Field(None, ge=1, le=65535)
    ism_secure: Optional[bool] = Field(True)
class Metrics(BaseModel):
    name: StrictStr

class Config(BaseModel):
    parameters: Parameters
    metrics: List[Metrics]
    ips: List[Ip]

class SystemsName(BaseModel):
    name: StrictStr
    resources_types: StrictStr
    config: Config

class GlobalParameters(BaseModel):
    repository: StrictStr
    repository_port: PositiveInt
    repository_protocol: Literal['tcp', 'udp']
    loglevel: Literal['NOTSET', 'INFO', 'WARNING', 'DEBUG', 'ERROR', 'CRITICAL']
    logfile: StrictStr

class ConfigFile(BaseModel):
    systems: List[SystemsName]
    global_parameters: GlobalParameters
########## CLASS FROM PYDANTIC TO VALIDATE YAML SCHEMA ##########################

########## FUNCTION VALIDATES YAML AND RETURNS DICT #############################
def create_metric_ip_dicts(config):
    result_dicts = []
    global_parms = config.global_parameters
    for system in config.systems:
        for metric in system.config.metrics:
            for ip in system.config.ips:
                ip_dict = vars(ip)
                result_dict = {
                    "name": system.name,
                    "resources_types": system.resources_types,
                    **system.config.parameters.model_dump(),
                    "metric_name": metric.name,
                    "ip": ip.ip,
                    **ip_dict,
                    "func": AllowedMetrics.get_func_name(system.resources_types, metric.name),
                    **global_parms.model_dump()
                }
                result_dicts.append(result_dict)
                
    return result_dicts, global_parms.model_dump()
########## FUNCTION VALIDATES YAML AND RETURNS DICT #############################

########## FUNCTION READ YAML AND PASS IT TO PYDANTIC CLASS #####################
def read_yaml(file_path: str) -> ConfigFile:
    with open(file_path, 'r') as stream:
        config = yaml.safe_load(stream)
    
    return ConfigFile(**config)
########## FUNCTION READ YAML AND PASS IT TO PYDANTIC CLASS #####################