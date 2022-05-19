import cloudshell.helpers.scripts.cloudshell_scripts_helpers as helpers
from cli_handler import LinuxSSH
from cloudshell.logging.qs_logger import get_qs_logger

def _get_ssh_session_from_context(api):
    """
    destructure context and return ssh session

    :param CloudShellAPISession api:
    :return:
    """

    reservationId = helpers.get_reservation_context_details().id
    resource_name = helpers.get_resource_context_details().name
    model = helpers.get_resource_context_details().model
    private_ip = helpers.get_resource_context_details().address


    user = api.GetAttributeValue(resource_name, "{}.User".format(model)).Value
    encrypted_password = api.GetAttributeValue(resource_name, "{}.Password".format(model)).Value
    decrypted_password = api.DecryptPassword(encrypted_password).Value

    ssh_port = 22

    if not decrypted_password:
        exc_msg = f"No password populated for '{resource_name}'. Can't get SSH session"
        raise ValueError(exc_msg)

    ssh = LinuxSSH(address=private_ip, username=user, password=decrypted_password, port=ssh_port)
    return ssh


def health_check(api):
    """
    SSH session test
    :param CloudShellAPISession api:
    :return:
    """

    reservationId = helpers.get_reservation_context_details().id
    logger = get_qs_logger(log_category="SSH_health_check", log_group=reservationId,
                                     log_file_prefix='SSH_health_check')
    resource_name = helpers.get_resource_context_details().name
    api.WriteMessageToReservationOutput(reservationId=reservationId,
                                        message='Run health_check on {}'.format(resource_name))

    ssh = _get_ssh_session_from_context(api)
    logger.info("Sending SSH command: '{}'".format(resource_name))

    try:
        cli_user_outp = ssh.send_command("whoami")
    except Exception as e:
        err_msg = f"Issue running health check to {resource_name}. {type(e).__name__}: {str(e)}"
        logger.error(err_msg)
        api.SetResourceLiveStatus(resource_name, "Error", err_msg)
        raise Exception(err_msg)

    current_user = cli_user_outp.split("\n")[0].strip()
    success_msg = f"SSH Health check passed. Current running user: {current_user}"
    api.SetResourceLiveStatus(resource_name, "Online", success_msg)
    return success_msg

def main():

    try:

        api = helpers.get_api_session()

        health_check(api)
    except:
        raise ValueError("Failed to run SSH health check")


if __name__ == "__main__":
    main()


