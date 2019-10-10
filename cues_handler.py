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

from uuid import uuid4

from lisp.plugins.cart_layout.layout import CartLayout
from lisp.plugins.list_layout.layout import ListLayout
from lisp.ui.ui_utils import translate

class CuesHandler:

    def __init__(self):
        self._cuelists = {}
        self._cuelist_order = []

    def register_cuelists(self, session_layout): # session_layout == self.app.layout @ plugin-level
        self._cuelists = {}

        if isinstance(session_layout, ListLayout):
            # LiSP doesn't support multiple cue lists in List Layout
            # Thus, we create a single dict encapsulating all cues
            self._create_cuelist('cuelist', 'Main Cue List')

        if isinstance(session_layout, CartLayout):
            # We create a dict for each cart tab page
            for page in session_layout.view.pages():
                index = session_layout.view.indexOf(page)
                name = session_layout.view.tabTexts()[index]
                self._create_cuelist('cuecart', name)

    def get_cuelists(self):
        cuelists = []
        for uuid in self._cuelist_order:
            cuelists.append(self._cuelists[uuid])
            # todo: populate cue array
        return cuelists

    def _create_cuelist(self, typename, name):
        uuid = str(uuid4())
        cuelist = {
            'uniqueID': uuid, # string
            'number': str(-len(self._cuelist_order) - 1), # string
            'name': name, # string
            'listName': name, # string
            'type': typename, # string; cuelist or cuecart
            'colorName': 'none', # string
            'flagged': 0, # number
            'armed': 1, # number
            'cues': []
        }
        self._cuelists[uuid] = cuelist
        self._cuelist_order.append(uuid)

