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
from threading import Lock

from liblo import ServerError, ServerThread, TCP

from lisp.core.signal import Signal
from lisp.core.util import get_lan_ip
from lisp.ui.ui_utils import translate

logger = logging.getLogger(__name__)

class OscTcpServer:

    def __init__(self, port):
        self._port = port
        self._srv = None
        self._running = False
        self._lock = Lock()
        self._methods = []

        self.new_message = Signal()

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, port):
        self._port = port
        self.stop()
        self.start()

    @property
    def ip(self):
        return get_lan_ip()

    @property
    def url(self):
        return self._srv.url if self._running else None

    def is_running(self):
        return self._running

    def register_method(self, callback, path=None, types=None):
        self._methods.append((callback, path, types))

    def start(self):
        if self._running:
            return

        try:
            self._srv = ServerThread(self._port, TCP)
            for method in self._methods:
                self._srv.add_method(method[1], method[2], method[0])
            self._srv.add_method(None, None, self.new_message.emit, self._srv)
            self._srv.start()
            
            self._running = True
            
            logger.info(
                translate(
                    "OscServerInfo", "OSC server started at {}"
                ).format(self._srv.url)
            )
        except ServerError:
            logger.exception(
                 translate("OscServerError", "Cannot start OSC server")
            )

    def stop(self):
        if self._srv is not None:
            with self._lock:
                if self._running:
                    self._srv.stop()
                    self._running = False

            self._srv.free()
            logger.info(translate("OscServerInfo", "OSC server stopped"))

    def send(self, address, path, *args):
        if not address.hostname:
            return False

        with self._lock:
            if self._running:
                self._srv.send(address, path, *args)
        return True
