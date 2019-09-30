# -*- coding: utf-8 -*-
#
# This file is a derivation of work on - and as such shares the same
# licence as - Linux Show Player
#
# Linux Show Player:
#   Copyright 2012-2019 Francesco Ceruti <ceppofrancy@gmail.com>
#
# This file:
#   Copyright 2019 s0600204
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

from json import JSONEncoder
import logging

# pylint: disable=no-name-in-module
from liblo import ServerThread, ServerError, TCP

# pylint: disable=import-error
from lisp.core.plugin import Plugin
from lisp.core.util import get_lan_ip
from lisp.ui.ui_utils import translate

from .osc_tcp_server import OscTcpServer

logger = logging.getLogger(__name__) # pylint: disable=invalid-name

QLAB_TCP_PORT = 53000
QLAB_STATUS_OK = 'ok'
QLAB_STATUS_NOT_OK = 'error'

class QlabMimic(Plugin):
    """LiSP pretends to be QLab for the purposes of basic OSC control"""

    Name = 'QLab OSC Mimic'
    Authors = ('s0600204',)
    Depends = ('Osc',)
    Description = 'LiSP pretends to be QLab for the purposes of basic OSC control.'

    def __init__(self, app):
        super().__init__(app)

        self._encoder = JSONEncoder(separators=(',', ':'))

        self._server = OscTcpServer(QLAB_TCP_PORT)
        self._server.start()
        self._server.new_message.connect(self.response_handler)

    @property
    def server(self):
        return self._server

    def terminate(self):
        self._server.stop()

    def finalize(self):
        logger.debug('Shutting down QLab server')
        self.terminate()

    def response_handler(self, path, args, types, src, user_data):
        src.set_slip_enabled(True)
        response = {
            'address': path,
            'status': QLAB_STATUS_OK,
            'data': self.response_workspaces(),
        }
        response = self._encoder.encode(response)
        self._server.send(src, '/reply' + path, response)

    def response_workspaces(self):
        return [{
            'uniqueID': 'lisp_workspace',
            'displayName': 'LiSP Showfile',
            'hasPasscode': 0,
            'version': '0.1',
        }]
