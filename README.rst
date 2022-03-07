QLab OSC Mimic
==============

Description
-----------

The **QLab OSC Mimic** is a community-created plugin for `Linux Show Player`_
(LiSP).

This plugin causes LiSP to respond to some of the same OSC messages that 
allow remote control of QLab.

This idea is that this should allow the use of mobile-device apps designed
for the purpose of remote controlling QLab to also control LiSP.


Remote Apps
"""""""""""

The following apps are known about and work with the **QLab OSC Mimic** plugin
(to some limited degree):

`QLab Remote`_
  (iOS / iPadOS)

  The official iOS/iPadOS app from Figure53_, the people who created QLab.

  The app is available for free from the iOS/iPadOS App Store, however this is
  restricted to Read-Only mode. To enable remote control, one must pay an in-app
  purchase. At the time of writing, this is roughly USD$39.99.

`Audio Toolbox`_
  (iPadOS)

  A free (but not Open Source) third party app with many useful features, QLab
  control being one of them.

  .. note:: At present this app does not support Carts properly, displaying cues
            as a list.

`Q Surface`_
  (iOS / iPadOS)

  A free (but not Open Source) third party app that can be used to adjust the
  control points of video surfaces used by QLab.

  .. note:: As LiSP doesn't currently output the visual component of video files
            it plays, there's no real point to using this with LiSP.

Incompatible apps
'''''''''''''''''

`Q GO`_
  (iOS / iPadOS)

  A free (but not Open Source) app designed to be used with QLab versions 2 and
  3. As such it uses MIDI to control QLab, not OSC. (And communication is
  one-way.)

`qControl`_
  (iOS / Android)

  A free (but not Open Source) app with a limited interface. Could be useful as
  a "GO" button for calling cues from a cue stack.
  
  .. note:: This app does not support Carts.

  .. note:: It is not possible for this app to discover LiSP shows available:
            the app looks for workspaces that are available for control with
            OSC-over-UDP only. (But then uses OSC-over-TCP to control them.)

  .. warning:: This app does not correctly disconnect itself from running
               workspaces, nor does it handle disconnect notifications from QLab
               or LiSP.

  .. note:: This app is not Open Source, however the project developer's website
            states that the underlying (.NET) toolkit is available on GitHub. If
            it is, it's not within a public repository.

  .. note:: This app is confused:

            First, it only "discovers" workspaces advertised as controllable via
            UDP, but then uses TCP when trying to interact with them.

            Second, it requires all OSC messages it *receives* to be "double END
            SLIP" encoded, but doesn't *send* OSC messages encoded this way.

  .. warning:: The app's menus are unreadable on iPadOS.

  .. note:: I have only tested on iPadOS.

`MiniStatus`_
  (iOS / iPadOS)

  A third-party app (requiring an in-app purchase if you wish to use it for more
  than three minutes at a time) that displays the status of various network
  attached devices and QLab workspaces.

  .. warning:: Emits malformed OSC.

  Specifically: it omits the OSC Type Tag. According to the OSC v1.0 spec
  (written 2002), this is indicative of an "older" implementation.

  According to the App Store, **MiniStatus** was first released 4th August 2020.
  This means that it is using an OSC implementation that is considered "old" by
  a specification that was itself 18 years old when the app was released.

  Needless to say, our OSC library is much newer, and thus rejects the
  non-standard OSC messages emitted by **MiniStatus**.


Installation
------------

To install and use this plugin for LiSP, there are a couple of steps.

Dependencies
""""""""""""

**Linux Show Player**
  Specifically, there are some modifications made to LiSP's code-base that
  support the plugin. For ease of acquisition, clone
  https://github.com/s0600204/linux-show-player.git (or add it as a remote to a
  preexisting clone) and recall the "show" branch. You will need to run LiSP
  from this branch.

**liblo**
  The minimum required version of liblo_ to run this plugin is ``0.31``.

  Unfortunately, only a handful of Linux distributions (at the time of writing)
  offer this version (or better). To overcome this, you will need to acquire the
  source, then compile and install it manually (you may need to remove the
  package provided by your distribution's package repositories).

**pyliblo**
  Regrettably, the maintainer(s) of this dependency have not updated their
  project since 2015. And we will need a more recent version than that made
  public by the project maintainers, let alone provided by the PyPI or any
  Linux distribution.

  From the provided link (pyliblo_), clone the master branch of the source code
  repository, then merge both currently outstanding Pull Requests (#17 & #22) as
  we need the changes contained within both. Follow the instructions of the
  project's README to build and install. Depending on your chosen flavour of
  Linux, you may need to remove your distribution's package first.

**python-zeroconf**
  Installable from pypi: https://pypi.org/project/zeroconf/, or from GitHub:
  https://github.com/jstasiak/python-zeroconf. Your distribution might also have
  a suitable package in its repositories.


Installation
""""""""""""

Once ready, navigate to ``$XDG_DATA_HOME/LinuxShowPlayer/$LiSP_Version/plugins/``
(on most Linux systems ``$XDG_DATA_HOME`` is ``~/.local/share``), and create a
subfolder named ``qlab_mimic``.

Place the files comprising this plugin into this new folder.

When you next start **Linux Show Player**, the program should load the plugin
automatically.


.. _Linux Show Player: https://github.com/FrancescoCeruti/linux-show-player
.. _QLab Remote: https://qlab.app/qlab-remote/
.. _Figure53: https://figure53.com/
.. _Audio Toolbox: https://www.danielhiggott.com/the-audio-toolbox
.. _Q Surface: https://audioapps.nl/app/Q-Surface
.. _Q GO: https://audioapps.nl/app/Q-GO
.. _qControl: https://jwetzell.com/projects/qcontroller/
.. _MiniStatus: https://apps.apple.com/gb/app/ministatus/id1510960205
.. _liblo: https://github.com/radarsat1/liblo
.. _pyliblo: https://github.com/dsacre/pyliblo
