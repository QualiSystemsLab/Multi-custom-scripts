import cloudshell.helpers.scripts.cloudshell_scripts_helpers as helpers
import winrm

from cloudshell.logging.qs_logger import get_qs_logger

def _get_winrm_session_from_context(api):
    """
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

    if not decrypted_password:
        exc_msg = f"No password populated for '{resource_name}'. Can't get WinRM session"
        raise ValueError(exc_msg)

    s = winrm.Session(private_ip, auth=(user, decrypted_password))
    return s

def _get_hostname_winrm(winrm_session):
        """
        :param winrm.Session winrm_session:
        :return:
        """
        hostname = _send_winrm_command(winrm_session, "hostname")
        return hostname.strip()

def _send_winrm_command(winrm_session, command):
    """
    :param winrm.Session winrm_session:
    :param str command:
    :return:
    :rtype str:
    """
    response = winrm_session.run_ps(command)

    # validate response
    if response.status_code != 0:
        exc_msg = "pywinrm response error. status code: {}".format(response.status_code)
        if response.std_out:
            exc_msg += ", std-out: {}".format(response.std_out)
        if response.std_err:
            exc_msg += ", std-err: {}".format(response.std_err)
        raise Exception(exc_msg)

    return response.std_out.decode("utf-8")

def health_check(api):
    """
        :param CloudShellAPISession api:
        :return:
    """

    reservationId = helpers.get_reservation_context_details().id
    logger = get_qs_logger(log_category="WinRm_health_check", log_group=reservationId,
                                     log_file_prefix='WinRm_health_check')

    resource_name = helpers.get_resource_context_details().name
    logger.info('Run winrm health_check on {}'.format(resource_name))


    try:
        s = _get_winrm_session_from_context(api)
        hostname = _get_hostname_winrm(s)
    except Exception as e:
        err_msg = f"Issue running health check to {resource_name}. {type(e).__name__}: {str(e)}"
        logger.error(err_msg)
        raise Exception(err_msg)

    api.SetResourceLiveStatus(resource_name, "Online", "WinRM Health Check Passed")
    api.WriteMessageToReservationOutput(reservationId=reservationId,
                                        message=f"Health Check PASSED. Target hostname: '{hostname}'")


def main():
    try:
        api = helpers.get_api_session()
        health_check(api)
    except:
        raise ValueError("Failed to WinRM health check")


if __name__ == "__main__":
    main()


