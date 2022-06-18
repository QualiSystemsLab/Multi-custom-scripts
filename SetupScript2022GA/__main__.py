import time
import socket
from cloudshell.workflow.orchestration.app import App

from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.setup.default_setup_orchestrator import DefaultSetupWorkflow
from cloudshell.helpers.scripts.cloudshell_dev_helpers import attach_to_cloudshell_as

from execute_configurations import run_script_execution

maps = {"name": "Tali",
        "Game": "Tak1",
        "param1": "Val1",
        "param2": "Val2",
        "id": "555"
        }

def custom_configure_apps(sandbox, components):
    """
    :param Sandbox sandbox:
    :return:
    """
    sandbox.automation_api.WriteMessageToReservationOutput(sandbox.id, "custom_configure_apps")
    change_script(sandbox)
    run_script_execution(sandbox,maps)

def change_script(sandbox):
    sandbox.automation_api.WriteMessageToReservationOutput(sandbox.id, "change_script")

    inga_apps = sandbox.components.get_apps_by_name_contains("Inga")
    for app in inga_apps:

        sandbox.automation_api.WriteMessageToReservationOutput(sandbox.id, "changing")
        sandbox.apps_configuration.set_config_param(app=app,
                                                    alias= "hello1",
                                                    key = 'hostname',
                                                    value = "Italy")
        sandbox.apps_configuration.set_config_param(app=app,
                                                    alias="hello1",
                                                    key='name',
                                                    value="Rob")
        


if __name__ == "__main__":

    sandbox = Sandbox()

    sandbox.automation_api.WriteMessageToReservationOutput(sandbox.id, "start setup")
    DefaultSetupWorkflow().register(sandbox, enable_configuration=False)
    sandbox.workflow.add_to_configuration(custom_configure_apps, None)
    sandbox.execute_setup()
