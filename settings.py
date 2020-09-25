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

# pylint: disable=missing-docstring, invalid-name

# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QVBoxLayout,
)

# pylint: disable=import-error
from lisp.ui.settings.pages import SettingsPage

class QlabMimicSettings(SettingsPage):
    Name = "QLab Mimic"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setLayout(QVBoxLayout())

        self.settingsGroup = QGroupBox(self)
        self.settingsGroup.setTitle("QLab Mimic")
        self.settingsGroup.setLayout(QFormLayout())
        self.layout().addWidget(self.settingsGroup)

        self._service_announcement = QCheckBox()
        self.settingsGroup.layout().addRow('Enable Service Announcement:', self._service_announcement)

    def getSettings(self):
        return {
            'service_announcement': self._service_announcement.isChecked(),
        }

    def loadSettings(self, settings):
        self._service_announcement.setChecked(settings['service_announcement'])
