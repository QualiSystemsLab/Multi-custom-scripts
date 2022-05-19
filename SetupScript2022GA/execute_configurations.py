import time
import socket
from typing import Dict, List

from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.setup.default_setup_orchestrator import DefaultSetupWorkflow
from cloudshell.helpers.scripts.cloudshell_dev_helpers import attach_to_cloudshell_as
import json

from cloudshell.api.cloudshell_api import ReservationAppResource, AppConfigurationData, ConfigurationManagementData, ConfigParam, SandboxDataKeyValue
from cloudshell.workflow.orchestration.setup.default_setup_logic import DefaultSetupLogic

from multiprocessing.pool import ThreadPool


#Version 1.0.0

def run_script_execution(sandbox, maps):
    """
    :param Sandbox sandbox:
    :param dict mapping:
    """
    #create new configurations dict with the new inputs
    configurations = map_app_inputs(sandbox, maps)

    resources = [sandbox.automation_api.GetResourceDetails(x.Name)
                 for x in sandbox.automation_api.GetReservationDetails(sandbox.id).ReservationDescription.Resources]

    # new dict of priorities and apps
    configure_priority = calculate_priority(resources, sandbox)
    sandbox.logger.info(f"Configure priority list: {configure_priority}")

    # Run apps by priority
    run_config_mgmt_parallel(configurations, configure_priority, sandbox)

def map_app_inputs(sandbox, mapping) -> Dict[str, List[AppConfigurationData]]:
    """
    :param Sandbox sandbox:
    :param dict mapping:
    :return dict AppConfigurationData:
    """

    configurations : Dict[str, List[ConfigurationManagementData]] = {}

    for app_name, app_details in sandbox.components.apps.items():
        if app_details.app_request.app_resource is None:
            # App wasn't already deployed
            continue
        resource_name = app_details.deployed_app.Name
        configurations[resource_name] = []
        sandbox.logger.info(f"Adding Resource: '{app_name}' to App configuration")

        for config_management in app_details.app_request.app_resource.AppConfigurationManagements:

            inputs = config_management.ScriptParameters
            connection_method = config_management.ConnectionMethod
            config_name = config_management.Alias
            new_inputs = []
            # update inputs with new values based on mapping dict
            for script_input in inputs:
                input_name = script_input.Name
                input_value = script_input.Value

                if input_name in mapping:
                    sandbox.logger.info(f"Resource: '{app_name}' App Config Name: '{config_name}' "
                                        f"Input name: '{input_name}' has new value from mapping")
                    input_value = mapping[input_name]

                #adding all inputs to new dict - both the changed inputs and the ones that didn't changed
                #as we are going to use the new configuration dictionary
                new_inputs.append(ConfigParam(input_name, input_value))

            config_data = ConfigurationManagementData(config_name, new_inputs)
            configurations[resource_name].append(AppConfigurationData(resource_name, [config_data]))

    return configurations

def reboot_vm(sandbox, resource_name):
    """
    :param Sandbox sandbox:
    :param str resource_name:
    :return:
    """

    sandbox.automation_api.WriteMessageToReservationOutput(sandbox.id, "reboot_vm")
    try:
        sandbox.automation_api.PowerOffResource(sandbox.id, resource_name)

        sandbox.automation_api.PowerOnResource(sandbox.id, resource_name)

        # generic way to wait for the VM to be responsive
        sandbox.automation_api.ExecuteResourceConnectedCommand(sandbox.id, resource_name, "remote_refresh_ip",
                                                               "remote_connectivity")
    except:
        sandbox.logger.exception("Failed to reboot VM")
        sandbox.automation_api.WriteMessageToReservationOutput(sandbox.id,
                                                               f"Failed to reboot VM {resource.Name}")
        raise


def check_resource_port(address, port):
    """
       :param str address:
       :param str port:
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((address, port))
    # sandbox.logger.info(f"Result for {address}:{port} is {result}")
    return result


def wait_for_health_check(sandbox, resource, timeout, delay, port):
    """
    :param Sandbox sandbox:
    :param resource:
    :param timeout:
    :param delay:
    :param port:
    :return:
    """
    sandbox.automation_api.WriteMessageToReservationOutput(sandbox.id, "wait_for_health_check")
    checks_needed = 2
    resource = sandbox.automation_api.GetResourceDetails(resource)
    time_now = time.time()
    results = {resource.Name: 0}
    while (time.time() - time_now) < timeout:

        sandbox.logger.info(f"Testing resource '{resource.Name}', timeout left: {timeout - (time.time() - time_now)} with port {port}")
        try:
            result = check_resource_port(resource.Address, port)
            sandbox.logger.info(f"Result for resource '{resource.Name}': '{result}'")
            if result == 0:
                results[resource.Name] += 1
        except Exception as e:
            sandbox.logger.error(f"error getting status check from resource '{resource.Name}': {e}")

        if results[resource.Name] == checks_needed:
            sandbox.logger.info(f"Finished checking all resources. Results: {results}")
            return
        else:
            time.sleep(delay)

    else:
        msg = f"VM(s) are not ready after {timeout/60} minutes. please check the logs"
        sandbox.logger.error(msg)
        raise Exception(msg)

def find_resource_command(resource,sandbox,command_name):

    commands = sandbox.automation_api.GetResourceCommands(resource).Commands
    for command in commands:
        if command.Name == command_name:
            sandbox.logger.info(f"found command {command_name}")
            return True

    return False

def configure_app_with_reboot_healthcheck(resource,sandbox,configurations):
    """
    :param Resource:
    :param Sandbox sandbox:
    :param Dictionary of resource names and AppConfigurationData configurations:
    :return:
        """

    sandbox.automation_api.WriteMessageToReservationOutput(sandbox.id, "configure_apps_with_reboot_healthcheck")
    try:
        #Get configurations of one specific resource
        resource_app_configs = configurations.get(resource, None)
    except:
        sandbox.automation_api.WriteMessageToReservationOutput(sandbox.id,
                                                               f"invalid resource {resource}")
        raise
    #Running all configuration of this resource
    for app_config in resource_app_configs:
        config_fail = True
        count = 0
        commandInputs = []
        timeout_health_check = 120
        port = 9999

        while config_fail:
            try:
                count += 1

                sandbox.automation_api.WriteMessageToReservationOutput(sandbox.id,
                       f"check connectivity to VM {resource}")

                #Checking connectivity to VM!!
                if find_resource_command(resource,sandbox,"Winrm_health_check"):
                    sandbox.automation_api.WriteMessageToReservationOutput(sandbox.id, "check winrm")
                    sandbox.automation_api.ExecuteCommand(sandbox.id, resource, 'Resource', "Winrm_health_check",
                               commandInputs, printOutput=True)


                elif find_resource_command(resource,sandbox,"SSH_health_check"):
                    sandbox.automation_api.WriteMessageToReservationOutput(sandbox.id, "check ssh")
                    sandbox.automation_api.ExecuteCommand(sandbox.id,resource,'Resource', "SSH_health_check",
                                                          commandInputs, printOutput=True)


                config_fail = False
            except:
                if count<5:
                    time.sleep(60)
                    sandbox.automation_api.WriteMessageToReservationOutput(sandbox.id, f"Retry test connectivity...")
                else:
                    raise ValueError("Failed to run connectivity health_check")

        sandbox.automation_api.WriteMessageToReservationOutput(sandbox.id,
                                                               f"running configuration {app_config.ConfigurationManagementDatas[0].Alias}")

        DefaultSetupLogic.configure_apps(api=sandbox.automation_api, reservation_id=sandbox.id, logger=sandbox.logger,
                                         appConfigurationsData=app_config)
        reboot = False
        health_check = False

        #checking of need to reboot or health check after
        for config_param in app_config.ConfigurationManagementDatas[0].ConfigParams:
            if config_param.Name == "do_reboot" and config_param.Value and config_param.Value.lower() == "true":
                reboot = True
                sandbox.automation_api.WriteMessageToReservationOutput(sandbox.id,
                                f"rebooting {app_config.ConfigurationManagementDatas[0].Alias}")

            elif config_param.Name == "health_check" and config_param.Value and config_param.Value.lower() == "true":
                health_check = True

        #check if we have additional attributes needed for health check
        if health_check:
            for config_param in app_config.ConfigurationManagementDatas[0].ConfigParams:
                if config_param.Name == "health_check_port" and config_param.Value:
                    try:
                        sandbox.logger.info(f"input port: {config_param.Value}")

                        port = int(config_param.Value)
                    except:
                        sandbox.automation_api.WriteMessageToReservationOutput(sandbox.id,
                                                                           f"Invalid port number in app {resource}")
                        raise

                elif config_param.Name == "Timeout_health_check":
                    if config_param.Value:
                        try:
                            timeout_health_check = int(config_param.Value)
                        except:
                            sandbox.automation_api.WriteMessageToReservationOutput(sandbox.id,f"Invalid timeout value in app {resource}")
                            raise

        if reboot:
            reboot_vm(sandbox, resource)
        if health_check:
            sandbox.automation_api.WriteMessageToReservationOutput(sandbox.id,
                     f"port  {port}")

            wait_for_health_check(sandbox, resource, timeout_health_check, 30, int(port))


def get_attribute_from_resource(sandbox, resource_name, attribute_name):
    """
    :param Sandbox sandbox:
    :param resource:
    :param attribute_name:
    :return:
    """
    resource_details = sandbox.automation_api.GetResourceDetails(resource_name)
    for attribute in resource_details.ResourceAttributes:
        if attribute.Name == attribute_name or attribute.Name.endswith(f".{attribute_name}"):
            return attribute.Value
    return None


def run_config_mgmt_parallel(configurations,configure_priority, sandbox):
    """
        :param dict configurations:
        :param dict configure_priority:
        :param :Sandbox sandbox
        :return:
     """


    # Run all configurations of apps on the same priority in parallel.
    for priority, resources_to_configure in sorted(configure_priority.items()):
        sandbox.logger.info(f"Working on configure priority: {priority}")

        try:
            pool = ThreadPool(len(resources_to_configure))
            async_results = [pool.apply_async(configure_app_with_reboot_healthcheck, (resource,sandbox,configurations))
                             for resource in resources_to_configure]

            pool.close()
            pool.join()

            # check results for errors
            for async_result in async_results:
                try:
                    # if thread ended with error get() will raise an exception
                    async_result.get()
                except Exception:
                    sandbox.logger.exception("error in configuring apps")

            if any(filter(lambda x: not x.successful(), async_results)):
                raise Exception("Error Configure_Reboot_Healthcheck app. Look at the logs for more details.")

            sandbox.automation_api.WriteMessageToReservationOutput(sandbox.id, "Configured VM successfully")

        except:
            sandbox.logger.exception("Failed to run configuration Manegment ")
            raise


def calculate_priority(resources, sandbox) -> Dict[int, List[str]]:
    """
       :param Sandbox sandbox:
       :param resource:
    """
    priority_dict: Dict[int, List[str]] = {}

    for resource in resources:
        priority_att = \
            next(filter(lambda x: x.Name == f"{resource.ResourceModelName}.Priority", resource.ResourceAttributes),
                 None)
        if priority_att:
            if priority_att.Value:
                try:
                    priority = int(priority_att.Value)
                    sandbox.logger.info(f"App resource: '{resource.Name}' has priority value of: {priority_att.Value}")
                except:
                    #To do- take default instead of exception and write the right msg
                    sandbox.automation_api.WriteMessageToReservationOutput(sandbox.id, f"Invalid priority value in app {resource.Name}")
                    raise
            else:
                priority = 10
                sandbox.logger.info(f"App resource: '{resource.Name}' has no priority value. setting default of 10")

        else:
            priority = 10
            sandbox.logger.info(f"App resource: '{resource.Name}' has no priority value. setting default of 10")

        if priority not in priority_dict:
            priority_dict[priority] = []
        priority_dict[priority].append(resource.Name)

    return priority_dict
