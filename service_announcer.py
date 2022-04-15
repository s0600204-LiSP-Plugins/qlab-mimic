# This file is a derivation of work on - and as such shares the same
# licence as - Linux Show Player
#
# Linux Show Player:
#   Copyright 2012-2022 Francesco Ceruti <ceppofrancy@gmail.com>
#
# This file:
#   Copyright 2022 s0600204
#
# Linux Show Player is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Linux Show Player is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Linux Show Player.  If not, see <http://www.gnu.org/licenses/>.

import logging
import socket
from threading import Lock

from zeroconf import IPVersion, ServiceInfo, Zeroconf

from lisp.core.decorators import async_function
from lisp.core.util import get_lan_ip
from lisp.ui.ui_utils import translate

logger = logging.getLogger(__name__)


class QLabServiceAnnouncer:

    ip_version = IPVersion.V4Only
    service_type = "_qlab._tcp.local."

    def __init__(self, port):
        self._lock = Lock()
        self._running = False
        self._service = None
        self._port = port

        self._zconf_instance = Zeroconf(
            ip_version=self.ip_version
        )

        self.build_service()

    def build_service(self):
        self._service = ServiceInfo(
            self.service_type,
            f"{socket.getfqdn(get_lan_ip())} [Linux Show Player].{self.service_type}",
            addresses=[socket.inet_pton(socket.AF_INET, get_lan_ip())],
            port=self._port
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
