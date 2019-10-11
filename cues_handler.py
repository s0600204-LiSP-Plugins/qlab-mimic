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

from lisp.cues.cue import CueState
from lisp.cues.cue_model import CueModel
from lisp.plugins.cart_layout.layout import CartLayout
from lisp.plugins.list_layout.layout import ListLayout
from lisp.ui.ui_utils import translate

from .pseudocues import CueCart, CueList
from .utility import QlabStatus

logger = logging.getLogger(__name__) # pylint: disable=invalid-name

TARGETS_FILES = ['GstMediaCue']
TARGETS_OTHER_CUES = ['CollectionCue', 'IndexActionCue', 'SeekCue', 'VolumeControl']

class CuesHandler:

    def __init__(self):
        self._cuelists = CueModel()

    def register_cuelists(self, session_layout): # session_layout == self.app.layout @ plugin-level
        self._cuelists.reset()

        if isinstance(session_layout, ListLayout):
            # LiSP doesn't support multiple cue lists in List Layout
            # Thus, we create a single object encapsulating all cues
            self._cuelists.add(CueList())

        if isinstance(session_layout, CartLayout):
            # We create an object for each cart tab page
            for page in session_layout.view.pages():
                index = session_layout.view.indexOf(page)
                name = session_layout.view.tabTexts()[index]
                self._cuelists.add(CueCart(name, index))

    def get_cuelists(self):
        cuelists = []
        for container in self._cuelists:
            cuelists.append({
                'uniqueID': container.id, # string
                'number': container.index, # string
                'name': container.name, # string
                'listName': container.name, # string
                'type': container.type.lower(), # string; cuelist or cuecart
                'colorName': 'none', # string
                'flagged': 0, # number
                'armed': 1, # number
                'cues': [],
            })
        return cuelists

    def by_cue_id(self, path, args, cue_model):
        # determine cue based on cue id
        cue = self._cuelists.get(path[1]) or cue_model.get(path[1])
        if cue is None:
            return (QlabStatus.NotOk, None)
        del path[0:2]
        return self._cue_common(cue, path, args)

    def by_cue_number(self, path, args, cue_model):
        # determine cue based on cue number
        cue = None
        if path[1] == 'L': # ListLayout CueList
            cue = list(self._cuelists.items())[0][1]
        elif path[1].startsWith('P'): # CartLayout Page
            cue = self._cuelists.get(list(self._cuelists.keys())[path[1][1:]])
        else:
            cue = cue_model.items[int(path[1])][1]

        if cue is None:
            return (QlabStatus.NotOk, None)
        del path[0:2]
        return self._cue_common(cue, path, args)

    def _cue_common(self, cue, path, args):
        # Handle requests for a cue to start, stop, etc.
        # Handled first as these are more important than getting/setting cue properties
        handled = self._cue_do(cue, path, args)
        if handled:
            return (QlabStatus.Ok, None)

        # Handle requests that get information
        info = self._cue_info_get(cue, path) if not args else None
        if info is not None:
            return (QlabStatus.Ok, info)

        # Handle requests that set information
        handled = self._cue_info_set(cue, path, args)
        if handled:
            return (QlabStatus.Ok, None)

        # If we've got this far, we don't support or recognise the request
        return (QlabStatus.NotOk, None)

    def _cue_info_get(self, cue, path):
        return {
            'armed': True,
            'currentDuration': cue.duration,
            'defaultName': translate('CueName', cue.Name),
            'displayName': cue.name,
            'fileTarget': None if cue.type != 'GstMediaCue' else cue.input_uri, # @todo check the appropriate property
            'hasCueTargets': True if cue.type in TARGETS_OTHER_CUES else False,
            'hasFileTargets': True if cue.type in TARGETS_FILES else False,
            'isActionRunning': cue.state == CueState.Running,
            'isBroken': cue.state == CueState.Error,
            'isFlagged': False,
            'isLoaded': True,
            'isOverridden': False, # whether a cue's output is suppressed by an override control
            'isPanicking': False, # is fading out during a 'panic' (all stop)
            'isPaused': cue.state == CueState.IsPaused,
            'isRunning': cue.state == CueState.IsRunning,
            'isTailingOut': False, # if cue has an AudioUnit which is decaying
            'listName': '* {} *'.format(cue.name),
            'name': cue.name,
            'notes': cue.description,
            'number': str(cue.index),
            'playbackPosition': 'none', # Same as `playbackPositionId`. See note for that
            'playbackPositionId': 'none', # CueList: UUID of current selected cue; CueCart: 'none'; no other cue should support this.
            'type': self._derive_qlab_cuetype(cue),
            'uniqueID': cue.id,
        }.get(path[0], None)

    def _cue_info_set(self, cue, path, args):
        #if path[0] == 'armed': # Cues cannot be disarmed in LiSP

        if path[0] == 'name':
            cue.name = args[0] # @todo VALIDATE THIS! well it's of limited charset as it has to pass over osc, so... what's the range of legitimate chars?
            return True

        if path[0] == 'notes':
            cue.description = args[0]
            return True

        #if path[0] == 'number': # LiSP does not allow changing cue numbers

        return False

    def _cue_do(self, cue, path, args):
        if cue.state == CueState.Error:
            return False

        # (Technically, 'go' should only work on CueLists)
        if path[0] == 'start' or path[0] == 'startAndAutoloadNext' or path[0] == 'go':
            if cue.state != CueState.IsRunning:
                cue.start(fade=True)
            return True

        if path[0] == 'pause' or path[0] == 'hardPause':
            if cue.state != CueState.IsPaused:
                cue.pause(fade=path[0] == 'pause')
            return True

        if path[0] == 'resume':
            if cue.state == CueState.IsPaused:
                cue.resume(fade=True)
            return True

        if path[0] == 'togglePause':
            if cue.state == CueState.IsPaused:
                cue.resume(fade=True)
            elif cue.state != CueState.IsPaused:
                cue.pause(fade=True)
            return True

        if path[0] == 'stop' or path[0] == 'hardStop':
            if cue.state != CueState.IsStopped:
                cue.stop(fade=path[0] == 'stop')
            return True

        return False

    def _derive_qlab_cuetype(self, cue):
        # QLab Cue Types:
        #     audio, mic, video, camera, text, light, fade, network, midi,
        #     midi file, timecode, group, start, stop, pause, load, reset,
        #     devamp, goto, target, arm, disarm, wait, memo, script, list,
        #     cuelist, cue list, cart, cuecart, or cue cart.
        cue_type = {
            'CollectionCue': None,
            'CommandCue': None,
            'CueCart': 'cuecart',
            'CueList': 'cuelist',
            #'DcaAssignCue': None,
            #'DcaResetCue': None,
            #'FixtureControlCue': None,
            'GstMediaCue': 'audio',
            'IndexActionCue': None,
            'MidiCue': 'midi',
            'OscCue': 'network',
            'SeekCue': None,
            'StopAll': None,
            'VolumeControl': 'fade',
        }.get(cue.type, None)
        if cue_type is None:
            logger.debug('Cue type {} needs aliasing!'.format(cue.type))
            cue_type = 'script'
        return cue_type
