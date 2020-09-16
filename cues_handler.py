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

from ast import literal_eval
import logging

from lisp.cues.cue import CueState
from lisp.cues.cue_model import CueModel
from lisp.plugins.cart_layout.layout import CartLayout
from lisp.plugins.list_layout.layout import ListLayout
from lisp.ui.ui_utils import translate

from .pseudocues import CueCart, CueList
from .utility import QlabStatus

logger = logging.getLogger(__name__) # pylint: disable=invalid-name

# Other states: next, fadein_start, fadein_end, fadeout_start, fadeout_end
# (the latter four do not transmit `self`, so there's no easy way to tell which cue they were emitted from)
CUE_STATE_CHANGES = ['interrupted', 'started', 'stopped', 'paused', 'error', 'error_clear', 'end']

TARGETS_FILES = ['GstMediaCue']
TARGETS_OTHER_CUES = ['CollectionCue', 'IndexActionCue', 'SeekCue', 'VolumeControl']

# QLab Cue Types:
#   audio, mic, video, camera, text, light, fade, network, midi,
#   midi file, timecode, group, start, stop, pause, load, reset,
#   devamp, goto, target, arm, disarm, wait, memo, script, list,
#   cuelist, cue list, cart, cuecart, or cue cart
CUE_TYPE_MAPPING = {
    'CollectionCue': None,
    'CommandCue': None,
    'CueCart': 'Cart',
    'CueList': 'Cue List',
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
}

class CuesHandler:

    def __init__(self, plugin):
        self._cuelists = CueModel()
        self._plugin = plugin
        self._session_layout = None

    def register_cuelists(self, session_layout): # session_layout == self.app.layout @ plugin-level
        self._cuelists.reset()
        self._session_layout = session_layout

        if isinstance(session_layout, ListLayout):
            # LiSP doesn't support multiple cue lists in List Layout
            # Thus, we create a single object encapsulating all cues
            self._cuelists.add(CueList(session_layout))

        elif isinstance(session_layout, CartLayout):
            session_layout.page_added.connect(self._on_cartpage_added)
            session_layout.page_removed.connect(self._on_cartpage_removed)

            # We create an object for each cart tab page
            for page in session_layout.view.pages():
                index = session_layout.view.indexOf(page)
                self._on_cartpage_added(index, page)

    def _on_cartpage_added(self, page_index, _):
        self._cuelists.add(CueCart(self._session_layout, page_index))
        self._plugin.emit_workspace_updated()

    def _on_cartpage_removed(self, page_index):
        pages = list(self._cuelists.items())
        page_removed = pages[page_index][1]
        self._cuelists.remove(page_removed)

        # Having removed the page, all subsequent ones have a new (internal) index
        subsequent_pages = pages[page_index + 1:]
        for page in subsequent_pages:
            page[1].set_index(page_index)
            self._plugin.emit_cue_updated(page[1])
            page_index += 1

        self._plugin.emit_workspace_updated()

    def get_cuelists(self):
        cuelists = []
        for container in self._cuelists:
            cuelists.append(self._cue_summary(container))
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
            cue = cue_model.items[int(path[1]) - 1][1]

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

        # Handle requests for an arbitrary collection of information about a cue
        if path[0] == 'valuesForKeys':
            data = {}
            for point in literal_eval(args[0]):
                value = self._cue_info_get(cue, [point])
                if value is None:
                    logger.debug('"{}" of cue (type: {}) requested'.format(point, cue.type))
                else:
                    data[point] = value
            return (QlabStatus.Ok, data)

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
            'armed': lambda: True,
            'cartColumns': lambda: cue.columns if cue.type == 'CueCart' else None,
            'cartPosition': lambda: self._get_cart_position(cue) if cue.type != 'CueCart' else [0, 0],
            'cartRows': lambda: cue.rows if cue.type == 'CueCart' else None,
            'children': lambda: self._cue_children(cue),
            'currentDuration': lambda: cue.duration,
            'defaultName': lambda: translate('CueName', cue.Name),
            'displayName': lambda: cue.name,
            'fileTarget': lambda: None if cue.type != 'GstMediaCue' else cue.input_uri, # @todo check the appropriate property
            'flagged': lambda: False,
            'hasCueTargets': lambda: cue.type in TARGETS_OTHER_CUES,
            'hasFileTargets': lambda: cue.type in TARGETS_FILES,
            'isActionRunning': lambda: cue.state == CueState.Running,
            'isBroken': lambda: cue.state == CueState.Error,
            'isLoaded': lambda: True,
            'isOverridden': lambda: False, # whether a cue's output is suppressed by an override control
            'isPanicking': lambda: False, # is fading out during a 'panic' (all stop)
            'isPaused': lambda: bool(cue.state & CueState.IsPaused),
            'isRunning': lambda: bool(cue.state & CueState.IsRunning),
            'isTailingOut': lambda: False, # if cue has an AudioUnit which is decaying
            'listName': lambda: '* {} *'.format(cue.name),
            'mode': lambda: 5 if cue.type == 'CueCart' else 0, # List: 0, Groups 1-4, Cart: 5
            'name': lambda: cue.name,
            'notes': lambda: cue.description,
            'number': lambda: str(cue.index + 1) if isinstance(cue.index, int) else cue.index,
            'parent': lambda: self._cue_parent_id(cue),
            'playbackPosition': lambda: cue.standby_cue_num() if cue.type == 'CueList' else 'none',
            'playbackPositionId': lambda: cue.standby_cue_id() if cue.type == 'CueList' else 'none',
            'type': lambda: self._derive_qlab_cuetype(cue),
            'uniqueID': lambda: cue.id,
        }.get(path[0], lambda: None)()

    def _cue_info_set(self, cue, path, args):
        #if path[0] == 'armed': # Cues cannot be disarmed in LiSP

        if path[0] == 'name':
            cue.name = args[0] # @todo VALIDATE THIS! well it's of limited charset as it has to pass over osc, so... what's the range of legitimate chars?
            return True

        if path[0] == 'notes':
            cue.description = args[0]
            return True

        #if path[0] == 'number': # LiSP does not allow changing cue numbers

        if path[0] == 'playbackPosition':
            if cue.type == 'CueList':
                try:
                    cue_num = int(args[0]) - 1
                except ValueError:
                    cue_num = args[0]
                cue.set_standby_num(cue_num)
                return True

        if path[0] == 'playbackPositionId':
            if cue.type == 'CueList':
                return cue.set_standby_id(args[0])

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

    def _cue_summary(self, cue):
        cue_obj = {
            'uniqueID': cue.id, # string
            'number': str(cue.index + 1) if isinstance(cue.index, int) else cue.index, # string
            'name': cue.name, # string
            'listName': cue.name, # string
            'type': self._derive_qlab_cuetype(cue), # string
            'colorName': 'none', # string
            'flagged': 'false', # number when setting, string when returning
            'armed': 'true', # number when setting, string when returning
        }
        if cue.type in ['CueCart', 'CueList']:
            cue_obj['cues'] = self._cue_children(cue)

        return cue_obj

    def _cue_children(self, cue):
        if cue.type not in ['CueCart', 'CueList']:
            return None
        cues = []
        cues_iter = None
        if cue.type == 'CueCart':
            cues_iter = self._session_layout.model.iter_page(int(cue.index[1:]) - 1)
        elif cue.type == 'CueList':
            cues_iter = self._session_layout.model

        try:
            for child in cues_iter:
                cues.append(self._cue_summary(child))
        except StopIteration:
            pass
        return cues

    def cue_parent(self, cue):
        first_parent = list(self._cuelists.items())[0][1]
        if isinstance(first_parent, CueList):
            return first_parent

        if isinstance(first_parent, CueCart):
            page_num = first_parent.position(cue)[0:1]
            return list(self._cuelists.items())[page_num][1]

        return None

    def _cue_parent_id(self, cue):
        if cue.type in ['CueCart', 'CueList']:
            return '[root group of cue lists]'

        parent = self.cue_parent(cue)
        if parent:
            return parent.id

        return 'none'

    def _derive_qlab_cuetype(self, cue):
        cue_type = CUE_TYPE_MAPPING.get(cue.type, None)
        if cue_type is None:
            logger.debug('Cue type {} needs aliasing!'.format(cue.type))
            cue_type = 'script'
        return cue_type

    def _get_cart_position(self, cue):
        parent = list(self._cuelists.items())[0][1]
        if isinstance(parent, CueCart):
            return parent.position(cue)[1:]
        return [0, 0]
