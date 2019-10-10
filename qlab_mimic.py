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
from uuid import uuid4

# pylint: disable=no-name-in-module
from liblo import ServerThread, ServerError, TCP

# pylint: disable=import-error
from lisp.core.plugin import Plugin
from lisp.core.util import get_lan_ip
from lisp.ui.ui_utils import translate

from .cues_handler import CuesHandler
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

        self._session_name = None
        self._session_uuid = None
        self._connected_clients = {}

        self._encoder = JSONEncoder(separators=(',', ':'))

        self._cues_message_handler = CuesHandler()

        self._server = OscTcpServer(QLAB_TCP_PORT)
        self._server.register_method(self._handle_workspaces, '/workspaces')
        self._server.start()
        self._server.new_message.connect(self._generic_handler)

    def _on_session_initialised(self, session):
        self._session_name = session.name()
        self._session_uuid = str(uuid4())

        self._cues_message_handler.register_cuelists(self.app.layout)

    @property
    def server(self):
        return self._server

    def terminate(self):
        self._server.stop()

    def finalize(self):
        logger.debug('Shutting down QLab server')
        self.terminate()

    def send(self, src, path, status, data):
        data['status'] = status
        data = self._encoder.encode(data)
        self._server.send(src, path, data)

    def send_reply(self, src, path, status, data=None, send_id=True):
        src.set_slip_enabled(True)
        response = {
            'address': path,
            'status': status,
        }
        if send_id and self._session_uuid:
            response['workspace_id'] = self._session_uuid
        if status is QLAB_STATUS_OK and data is not None:
            response['data'] = data
        response = self._encoder.encode(response)
        self._server.send(src, '/reply' + path, response)

    def _generic_handler(self, original_path, args, types, src, user_data):
        path = split_path(original_path)

        handlers = {
            'workspace': self._handle_workspace,
        }

        if path[0] not in handlers:
            self.send_reply(src, original_path, QLAB_STATUS_NOT_OK)
            return

        handlers.get(
            path[0], lambda *_: None
        )(
            original_path, args, types, src, user_data
        )

    def _handle_connection(self, original_path, args, types, src, user_data):
        path = split_path(original_path)
        client_id = "{}:{}".format(src.hostname, src.port)

        if path[2] == 'connect':
            if client_id not in self._connected_clients:
                self._connected_clients[client_id] = [src, False]
            self.send_reply(src, original_path, QLAB_STATUS_OK, 'ok')
            return

        if path[2] == 'disconnect':
            if client_id in self._connected_clients:
                del self._connected_clients[client_id]
            else:
                logger.warn(client_id + " not recognised (disconnect)")
            self.send_reply(src, original_path, QLAB_STATUS_OK)
            return

        if path[2] == 'updates':
            if client_id not in self._connected_clients:
                self.send_reply(src, original_path, QLAB_STATUS_NOT_OK)
                return
            self._connected_clients[client_id][1] = bool(args[0])
            self.send_reply(src, original_path, QLAB_STATUS_OK)
            return

    def _handle_cuelists(self, path, args, types, src, user_data):
         cuelists = self._cues_message_handler.get_cuelists()
         self.send_reply(src, path, QLAB_STATUS_OK, cuelists)

    def _handle_thump(self, path, args, types, src, user_data):
        self.send_reply(src, path, QLAB_STATUS_OK, 'thump')

    def _handle_workspace(self, original_path, args, types, src, user_data):
        path = split_path(original_path)

         # If wrong workspace
        if path[1] != self._session_uuid and path[1] != self._session_name:
            self.send_reply(src, original_path, QLAB_STATUS_NOT_OK, send_id=False)
            return
        del path[0:2]

        handlers = {
            'connect': self._handle_connection,
            'cueLists': self._handle_cuelists,
            'disconnect': self._handle_connection,
            'thump': self._handle_thump,
            'updates': self._handle_connection,
        }

        if path[0] not in handlers:
            self.send_reply(src, original_path, QLAB_STATUS_NOT_OK)
            return

        handlers.get(
            path[0], lambda *_: None
        )(
            original_path, args, types, src, user_data
        )

    def _handle_workspaces(self, path, args, types, src, user_data):
        if not self._session_uuid:
            self.send_reply(src, path, QLAB_STATUS_NOT_OK, send_id=False)
            return

        workspaces = [{
            'uniqueID': self._session_uuid,
            'displayName': self._session_name,
            'hasPasscode': 0,
            'version': '0.1',
        }]

        self.send_reply(src, path, QLAB_STATUS_OK, workspaces, send_id=False)

def split_path(path):
    path = path.split('/')
    path.pop(0)
    return path
