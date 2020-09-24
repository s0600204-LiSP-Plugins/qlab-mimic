
import logging
import socket
from threading import Lock

from zeroconf import IPVersion, ServiceInfo, Zeroconf

from lisp.core.decorators import async_function
from lisp.core.util import get_lan_ip
from lisp.ui.ui_utils import translate

logger = logging.getLogger(__name__)

QLAB_TCP_PORT = 53000


class QLabServiceAnnouncer:

    ip_version = IPVersion.V4Only
    service_type = "_qlab._tcp.local."

    def __init__(self):
        self._lock = Lock()
        self._running = False
        self._service = None

        self._zconf_instance = Zeroconf(
            ip_version=self.ip_version
        )

        self.build_service()

    def build_service(self):
        self._service = ServiceInfo(
            self.service_type,
            f"Linux Show Player.{self.service_type}",
            addresses=[socket.inet_pton(socket.AF_INET, get_lan_ip())],
            port=QLAB_TCP_PORT
        )

    @async_function
    def start(self):
        if self._running:
            return

        with self._lock:
            self._zconf_instance.register_service(self._service)
            self._running = True
            logger.info(
                translate(
                    "QLabAnnouncer", "Starting announcement of QLab service."
                )
            )

    def stop(self):
        if not self._running:
            return

        with self._lock:
            self._running = False
            self._zconf_instance.unregister_service(self._service)
            logger.info(
                translate(
                    "QLabAnnouncer", "Stopping announcement of QLab service."
                )
            )

    def terminate(self):
        self.stop()
        self._zconf_instance.close()
