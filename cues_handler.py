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

from lisp.cues.cue_model import CueModel
from lisp.plugins.cart_layout.layout import CartLayout
from lisp.plugins.list_layout.layout import ListLayout
from lisp.ui.ui_utils import translate

from .pseudocues import CueCart, CueList

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
