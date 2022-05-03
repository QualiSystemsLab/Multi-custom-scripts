import time
import socket

from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.setup.default_setup_orchestrator import DefaultSetupWorkflow
from cloudshell.helpers.scripts.cloudshell_dev_helpers import attach_to_cloudshell_as

from execute_configurations import run_script_execution

maps = {"name": "name1",
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
    run_script_execution(sandbox,maps)


if __name__ == "__main__":

    sandbox = Sandbox()
    sandbox.automation_api.WriteMessageToReservationOutput(sandbox.id, "start setup")
    DefaultSetupWorkflow().register(sandbox, enable_configuration=False)
    sandbox.workflow.add_to_configuration(custom_configure_apps, None)
    sandbox.execute_setup()
