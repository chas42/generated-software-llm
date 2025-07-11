import logging
import requests

_MONITOR_URL = "http://localhost:{port}/monitor/commands"

def func_test_monitor(app) -> bool:
    port, logger = app.port, app.logger
    test_commands = ["grep", "ps.*", "grep.*", ".*yth.*"]
    filter_flags = [None, "aux", "a", "x", "a -T"]
    url_command = _MONITOR_URL.format(port=port)

    for command in test_commands:
        for filter_flag in filter_flags:
            logger.info(f"Sending request {command} / {filter_flag} to {url_command}")
            r = requests.post(
                url=url_command,
                json=(
                    {"command_regex": command, "filter_flags": filter_flag}
                    if filter_flag
                    else {"command_regex": command}
                ),
            )

            if not r.ok:
                logger.warning(
                    f"Failed to execute command '{command}' with status code {r.status_code} and message: '{r.text}'"
                )
                return False

            logger.info(f"got 200 response: {r.text}")

            response = r.json()
            if not isinstance(response, list) or not all(
                isinstance(item, dict)
                and "processId" in item
                and "processString" in item
                and isinstance(item["processId"], int)
                and isinstance(item["processString"], str)
                for item in response
            ):
                logger.warning(
                    f"Response for command '{command}' does not match the expected schema: {response}"
                )
                return False
    return True


# mock para o app com port e logger
class App:
    def __init__(self, port):
        self.port = port
        self.logger = logging.getLogger("api_test_logger")
        logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    app = App(port=3000)  # ajuste a porta conforme necessário
    success_monitor = func_test_monitor(app)
    print("Teste func_test_monitor passou?", success_monitor)
