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

import logging

# pylint: disable=no-name-in-module
from liblo import ServerThread, ServerError, TCP

# pylint: disable=import-error
from lisp.core.plugin import Plugin
from lisp.core.util import get_lan_ip
from lisp.plugins.osc.osc_server import OscServer
from lisp.ui.ui_utils import translate

logger = logging.getLogger(__name__) # pylint: disable=invalid-name

QLAB_TCP_PORT = 53000

class QlabMimic(Plugin):
    """LiSP pretends to be QLab for the purposes of basic OSC control"""

    Name = 'QLab OSC Mimic'
    Authors = ('s0600204',)
    Depends = ('Osc',)
    Description = 'LiSP pretends to be QLab for the purposes of basic OSC control.'

    def __init__(self, app):
        super().__init__(app)

        self._server = OscTcpServer(
            get_lan_ip(), QLAB_TCP_PORT, QLAB_TCP_PORT
        )
        self._server.start()

    @property
    def server(self):
        return self._server

    def terminate(self):
        self._server.stop()

    def finalize(self):
        logger.debug('Shutting down QLab server')
        self.terminate()

class OscTcpServer(OscServer):
    '''OSC Server that works on TCP instead of the default UDP

    The one and only method is a clone of the one in OscServer, but
    modified to use the TCP connection protocol instead of the default
    UDP.

    @todo: Create and submit PR upstream to LiSP to allow specifying protocol in OscServer
    '''

    # pylint: disable=invalid-name, no-member, access-member-before-definition, attribute-defined-outside-init
    def start(self):
        '''Clone of the function in OscServer, but set to establish a TCP connection'''
        if self._OscServer__running:
            return

        try:
            self._OscServer__srv = ServerThread(self._OscServer__in_port, TCP)
            self._OscServer__srv.add_method(None, None, self.new_message.emit)
            self._OscServer__srv.start()

            self._OscServer__running = True

            logger.info(
                translate("OscServerInfo", "OSC server started at {}").format(
                    self._OscServer__srv.url
                )
            )
        except ServerError:
            logger.exception(
                translate("OscServerError", "Cannot start OSC sever")
            )
