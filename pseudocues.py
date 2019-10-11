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

# pylint: disable=missing-docstring, invalid-name, too-few-public-methods

# pylint: disable=import-error
from lisp.cues.cue import Cue
from lisp.ui.ui_utils import translate

class CueCart(Cue):

    def __init__(self, name, index, **kwargs):
        super().__init__(**kwargs)
        self.name = translate('CueName', name)
        self.index = 'P' + str(index + 1)

class CueList(Cue):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = translate('CueName', 'Main Cue List')
        self.index = 'L'