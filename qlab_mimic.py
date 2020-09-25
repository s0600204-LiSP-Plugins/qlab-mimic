# -*- coding: utf-8 -*-
#
# This file is a derivation of work on - and as such shares the same
# licence as - Linux Show Player
#
# Linux Show Player:
#   Copyright 2012-2020 Francesco Ceruti <ceppofrancy@gmail.com>
#
# This file:
#   Copyright 2020 s0600204
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

# pylint: disable=import-error
from lisp.core.plugin import Plugin
from lisp.core.util import get_lan_ip
from lisp.plugins.list_layout.layout import ListLayout
from lisp.ui.settings.app_configuration import AppConfigurationDialog
from lisp.ui.ui_utils import translate

from .cues_handler import CuesHandler, CUE_STATE_CHANGES
from .osc_tcp_server import OscTcpServer
from .service_announcer import QLAB_TCP_PORT, QLabServiceAnnouncer
from .settings import QlabMimicSettings
from .utility import client_id_string, join_path, QlabStatus, split_path

logger = logging.getLogger(__name__) # pylint: disable=invalid-name

QLAB_VERSION = '4.3'

class QlabMimic(Plugin):
    """LiSP pretends to be QLab for the purposes of basic OSC control"""

    Name = 'QLab Mimic'
    Authors = ('s0600204',)
    Depends = ('Osc',)
    Description = 'LiSP pretends to be QLab for the purposes of basic OSC control.'

    def __init__(self, app):
        super().__init__(app)

        self._session_name = None
        self._session_uuid = None
        self._connected_clients = {}

        self._encoder = JSONEncoder(separators=(',', ':'))

        self._cues_message_handler = CuesHandler(self)

        self._server = OscTcpServer(QLAB_TCP_PORT)
        self._server.register_method(self._handle_always_reply, '/alwaysReply')
        self._server.register_method(self._handle_workspaces, '/workspaces')
        self._server.start()
        self._server.new_message.connect(self._generic_handler)

        self._server_announcer = QLabServiceAnnouncer()

        AppConfigurationDialog.registerSettingsPage(
            'plugins.qlab_mimic', QlabMimicSettings, self.Config)

        self.Config.updated.connect(self._actualize_config)
        self._actualize_config(self.Config)

    def _actualize_config(self, _):
        if self.Config.get("service_announcement", True):
            self._server_announcer.start()
        else:
            self._server_announcer.stop()

    def _on_session_initialised(self, session):
        self._session_name = session.name()
        self._session_uuid = str(uuid4())

        self.app.cue_model.item_added.connect(self._on_cue_added)
        self.app.layout.model.item_moved.connect(self._on_cue_moved)
        self.app.cue_model.item_removed.connect(self._on_cue_removed)

        if isinstance(self.app.layout, ListLayout):
            self.app.layout.view.listView.currentItemChanged.connect(self._emit_playback_head_updated)

        self._cues_message_handler.register_cuelists(self.app.layout)

    def _pre_session_deinitialisation(self, _):
        self._emit_workspace_disconnect()

        self._session_name = None
        self._session_uuid = None

        self.app.cue_model.item_added.disconnect(self._on_cue_added)
        self.app.layout.model.item_moved.disconnect(self._on_cue_moved)
        self.app.cue_model.item_removed.disconnect(self._on_cue_removed)

        if isinstance(self.app.layout, ListLayout):
            self.app.layout.view.listView.currentItemChanged.disconnect(self._emit_playback_head_updated)

        self._cues_message_handler.deregister_cuelists()

    @property
    def server(self):
        return self._server

    def terminate(self):
        self._server.stop()

    def finalize(self):
        logger.debug('Shutting down QLab server')
        self.terminate()
        self._server_announcer.terminate()

    def send_reply(self, src, path, status, data=None, send_id=True):
        client_id = client_id_string(src)
        if data is None and (client_id not in self._connected_clients or not self._connected_clients[client_id][2]):
            return
        src.set_slip_enabled(True)
        response = {
            'address': path,
            'status': status.value,
        }
        if send_id and self._session_uuid:
            response['workspace_id'] = self._session_uuid
        if status is QlabStatus.Ok and data is not None:
            response['data'] = data
        response = self._encoder.encode(response)
        self._server.send(src, '/reply' + path, response)

    def send_update(self, path, args=[], always_send=False):
        path[0:0] = ['update', 'workspace', self._session_uuid]
        path = join_path(path)
        for client in self._connected_clients.values():
            if client[1] or always_send:
                client[0].set_slip_enabled(True)
                self._server.send(client[0], path, *args)

    def _generic_handler(self, original_path, args, types, src, user_data):
        path = split_path(original_path)

        handlers = {
            'cue': self._handle_cue,
            'cue_id': self._handle_cue,
            'disconnect': self._handle_disconnect,
            'go': self._handle_go,
            'stop': self._handle_stop,
            'updates': self._handle_updates,
            'version': self._handle_version,
            'workspace': self._handle_workspace,
        }

        if path[0] not in handlers:
            self.send_reply(src, original_path, QlabStatus.NotOk)
            return

        handlers.get(
            path[0], lambda *_: None
        )(
            original_path, args, types, src, user_data
        )

    def _handle_always_reply(self, original_path, args, types, src, user_data):
        client_id = client_id_string(src)
        if client_id not in self._connected_clients:
            # No point in sending a reply, as we don't recognise the client
            return
        self._connected_clients[client_id][2] = bool(args[0])
        self.send_reply(src, original_path, QlabStatus.Ok)

    def _handle_connect(self, original_path, args, types, src, user_data):
        client_id = client_id_string(src)
        if client_id not in self._connected_clients:
            self._connected_clients[client_id] = [src, False, False]
        self.send_reply(src, original_path, QlabStatus.Ok, 'ok')

    def _handle_cue(self, original_path, args, types, src, user_data):
        path = split_path(original_path)
        if path[0] == 'workspace':
            del path[0:2]
        return_path = join_path(path)
        if path[0] == 'cue':
            status, data = self._cues_message_handler.by_cue_number(path, args, self.app.cue_model)
        else:
            status, data = self._cues_message_handler.by_cue_id(path, args, self.app.cue_model)
        self.send_reply(src, return_path, status, data)

    def _handle_cuelists(self, path, args, types, src, user_data):
         cuelists = self._cues_message_handler.get_cuelists()
         self.send_reply(src, path, QlabStatus.Ok, cuelists)

    def _handle_disconnect(self, original_path, args, types, src, user_data):
        client_id = client_id_string(src)
        if client_id in self._connected_clients:
            self.send_reply(src, original_path, QlabStatus.Ok)
            del self._connected_clients[client_id]
        else:
            logger.warn(client_id + " not recognised (disconnect)")

    def _handle_doubleGoWindowRemaining(self, path, args, types, src, user_data):
        self.send_reply(src, path, QlabStatus.Ok, 0)

    def _handle_go(self, path, args, types, src, user_data):
        self.app.layout.go()
        self.send_reply(src, path, QlabStatus.Ok)

    def _handle_runningCues(self, path, args, types, src, user_data):
        self._cues_message_handler.get_currently_playing(False)
        self.send_reply(src, path, QlabStatus.Ok, cues)

    def _handle_runningOrPausedCues(self, path, args, types, src, user_data):
        cues = self._cues_message_handler.get_currently_playing(True)
        self.send_reply(src, path, QlabStatus.Ok, cues)

    def _handle_selectionIsPlayhead(self, path, args, types, src, user_data):
        if isinstance(self.app.layout, ListLayout):
            if args:
                self.app.layout.selection_mode = not bool(args[0])
                self.send_reply(src, path, QlabStatus.Ok)
            else:
                self.send_reply(src, path, QlabStatus.Ok, int(not self.app.layout.selection_mode))

        else:
            if args:
                self.send_reply(src, path, QlabStatus.NotOk)
            else:
                self.send_reply(src, path, QlabStatus.Ok, 0)

    def _handle_showMode(self, path, args, types, src, user_data):
        if args:
            # We don't support changing this setting
            self.send_reply(src, path, QlabStatus.NotOk)
        else:
            self.send_reply(src, path, QlabStatus.Ok, 1)

    def _handle_stop(self, path, args, types, src, user_data):
        self.app.layout.stop_all()
        self.send_reply(src, path, QlabStatus.Ok)

    def _handle_thump(self, path, args, types, src, user_data):
        self.send_reply(src, path, QlabStatus.Ok, 'thump')

    def _handle_updates(self, original_path, args, types, src, user_data):
        client_id = client_id_string(src)
        if client_id not in self._connected_clients:
            # No point in sending a reply, as we don't recognise the client
            return
        self._connected_clients[client_id][1] = bool(args[0])
        self.send_reply(src, original_path, QlabStatus.Ok)

    def _handle_version(self, original_path, args, types, src, user_data):
        self.send_reply(src, original_path, QlabStatus.Ok, QLAB_VERSION)

    def _handle_workspace(self, original_path, args, types, src, user_data):
        path = split_path(original_path)

         # If wrong workspace
        if path[1] != self._session_uuid and path[1] != self._session_name:
            self.send_reply(src, original_path, QlabStatus.NotOk, send_id=False)
            return

        handlers = {
            'connect': self._handle_connect,
            'cue': self._handle_cue,
            'cue_id': self._handle_cue,
            'cueLists': self._handle_cuelists,
            'disconnect': self._handle_disconnect,
            'doubleGoWindowRemaining': self._handle_doubleGoWindowRemaining,
            'go': self._handle_go,
            'runningCues': self._handle_runningCues,
            'runningOrPausedCues': self._handle_runningOrPausedCues,
            'selectionIsPlayhead': self._handle_selectionIsPlayhead,
            'showMode': self._handle_showMode,
            'stop': self._handle_stop,
            'thump': self._handle_thump,
            'updates': self._handle_updates,
        }

        if path[2] not in handlers:
            self.send_reply(src, original_path, QlabStatus.NotOk)
            return

        handlers.get(
            path[2], lambda *_: None
        )(
            original_path, args, types, src, user_data
        )

    def _handle_workspaces(self, path, args, types, src, user_data):
        if not self._session_uuid:
            self.send_reply(src, path, QlabStatus.NotOk, send_id=False)
            return

        workspaces = [{
            'uniqueID': self._session_uuid,
            'displayName': self._session_name,
            'hasPasscode': 0,
            'version': QLAB_VERSION,
        }]

        self.send_reply(src, path, QlabStatus.Ok, workspaces, send_id=False)

    def _on_cue_added(self, cue):
        self.emit_workspace_updated()

        # Emit that the parent cue has been changed
        self.emit_cue_updated(self._cues_message_handler.cue_parent(cue))

        # Set listeners for when a cue has been edited...
        cue.properties_changed.connect(self.emit_cue_updated)
        # ...and when it changes state
        for state_change in CUE_STATE_CHANGES:
            cue.__getattribute__(state_change).connect(self.emit_cue_updated)

    def _on_cue_removed(self, cue):
        self.emit_workspace_updated()

        # Emit that the parent cue has been changed
        self.emit_cue_updated(self._cues_message_handler.cue_parent(cue))

        # Remove listeners for when a cue has been edited...
        cue.properties_changed.disconnect(self.emit_cue_updated)
        # ...and when it changes state
        for state_change in CUE_STATE_CHANGES:
            cue.__getattribute__(state_change).disconnect(self.emit_cue_updated)

    def _on_cue_moved(self, old_index, new_index):
        cue = self.app.layout.model.item(new_index)

        self.emit_workspace_updated()

        # Emit that the parent cue(s) have been changed
        self.emit_cue_updated(self._cues_message_handler.cue_parent(cue))
        if not isinstance(self.app.layout, ListLayout):
            # In case cue has been moved from one page to another
            old_page_num = self.app.layout.to_3d_index(old_index)[0]
            new_page_num = self.app.layout.to_3d_index(new_index)[0]
            if old_page_num != new_page_num:
                self.emit_cue_updated(self._cues_message_handler.cuelist(old_page_num))

    def emit_cue_updated(self, cue):
        '''Sent if the cue or its state has changed'''
        self.send_update(['cue_id', cue.id])

    def _emit_workspace_disconnect(self):
        '''Sent to tell clients that they need to disconnect

        e.g. because the workspace or application is being closed.
        '''
        self.send_update(['disconnect'], always_send=True)

    def emit_workspace_updated(self, *_):
        '''Sent if the cue lists for the workspace need reloading

        For instance when a cue is added, removed, or other aspects of a workspace are updated.
        '''
        self.send_update([])

    def _emit_playback_head_updated(self, selected, _):
        '''Sent if the the selected cue has changed'''
        cuelists = self._cues_message_handler.get_cuelists()
        self.send_update(
            ['cueList', cuelists[0]['uniqueID'], 'playbackPosition'],
            [selected.cue.id] if selected else []
        )
