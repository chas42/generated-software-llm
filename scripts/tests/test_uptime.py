import logging
import requests

def register_heartbeats(
    port: int,
    logger: logging.Logger,
    services: list[dict[str, str]],
) -> bool:
    for service in services:
        url = f"http://localhost:{port}/heartbeat"
        r = requests.post(url=url, json=service)
        if not r.ok:
            logger.warning("POST /heartbeat not ok: %d %s", r.status_code, r.reason)
            return False
    return True

def func_test_post_then_get(app) -> bool:
    port, logger = app.port, app.logger

    services = [
        {"token": "pass1", "serviceId": "svc1"},
        {"token": "pass2", "serviceId": "svc2"},
        {"token": "pass3", "serviceId": "svc3"},
        {"token": "pass4", "serviceId": "svc4"},
    ]

    if not register_heartbeats(port, logger, services):
        return False

    for token in ["pass1", "pass2", "invalid", "pass3", "pass4"]:
        url = f"http://localhost:{port}/services"
        r = requests.post(url=url, json={"token": token})
        if not r.ok:
            logger.warning("GET /messages not ok: %d %s", r.status_code, r.reason)
            return False

        logger.info("got response for GET /messages with token %s:\n%s", token, r.text)
        for service in services:
            if token == service["token"] and service["serviceId"] not in r.text:
                logger.warning(
                    "Service %s not found in response for token %s", service, token
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
    app = App(port=3000)  # <-- ajuste a porta se necessário
    success = func_test_post_then_get(app)
    print("Teste passou?" , success)