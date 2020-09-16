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

# pylint: disable=missing-docstring, invalid-name, too-few-public-methods

# pylint: disable=import-error
from lisp.cues.cue import Cue
from lisp.ui.ui_utils import translate

class CueCart(Cue):

    def __init__(self, layout, index, **kwargs):
        super().__init__(**kwargs)

        # `self.index` (inherited Property) is presented to Remote Apps (as the "cue number");
        # `self._index` is used internally within LiSP
        self._index = -1
        self._layout = layout

        self.set_index(index)

    @property
    def columns(self):
        return self._layout.view.widget(self._index).columns

    def position(self, cue):
        return list(self._layout.to_3d_index(int(cue.index)))

    @property
    def rows(self):
        return self._layout.view.widget(self._index).rows

    def set_index(self, index):
        self._index = index

    @property
    def index(self):
        return 'P' + str(self._index + 1)

    @property
    def name(self):
        return self._layout.view.tabText(self._index)

    def stop(self, **_):
        self._layout.stop_all()

class CueList(Cue):

    def __init__(self, layout, **kwargs):
        super().__init__(**kwargs)
        self.name = translate('CueName', 'Main Cue List')
        self.index = 'L'
        self._layout = layout

    def standby_cue_id(self):
        cue_num = self._layout.standby_index()
        if cue_num == -1:
            return 'none'
        return self._layout.cue_at(cue_num).id

    def standby_cue_num(self):
        cue_num = self._layout.standby_index()
        if cue_num == -1:
            return 'none'
        return str(cue_num)

    def set_standby_id(self, cue_id):
        for cue in self._layout.cues():
            if cue.id == cue_id:
                self._layout.set_standby_index(cue.index)
                return True
        return False

    def set_standby_num(self, cue_num):
        self._layout.set_standby_index(cue_num)

    def start(self, **_):
        self._layout.go()

    def stop(self, **_):
        self._layout.stop_all()
