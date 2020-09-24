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

The following apps are known about and work with this plugin (to some limited
degree):

`QLab Remote`_
  The official iOS/iPadOS app from Figure53_, the people who created QLab.

  The app is available for free from the iOS/iPadOS App Store, however this is
  restricted to Read-Only mode. To enable remote control, one must pay an in-app
  purchase. At the time of writing, this is roughly USD$39.99.

`Audio Toolbox`_
  A free third party app with many useful features, QLab control being one of
  them. Although free, the app is not Open Source. Also, the app's
  idiosyncrasies do not always conform to QLab's specification, so odd behaviour
  might occur.

  Please note that at present, this app does not support Carts properly,
  displaying cues as a list.

Incompatible apps
'''''''''''''''''

Q GO
  Uses MIDI, not OSC.



Installation
------------

To install and use this plugin for LiSP, there are a couple of steps.

Dependencies
""""""""""""

Linux Show Player.
  Specifically, there are some modifications made to LiSP's codebase that
  support the plugin. For ease of acquisition, clone
  https://github.com/s0600204/linux-show-player.git (or add it as a remote to a
  preexisting clone) and recall the "show" branch. You will need to run LiSP
  from this branch.

liblo
  The minimum required version of liblo_ to run this plugin is ``0.31``.

  Unfortunately, only a handful of Linux distributions (at the time of writing)
  offer this version (or better). To overcome this, you will need to acquire the
  source, then compile and install it manually (you may need to remove the
  package provided by your distribution's package repositories).

pyliblo
  Regrettably, the maintainer(s) of this dependency have not updated their
  project since 2015. And we will need a more recent version than that made
  public by the project maintainers, let alone provided by the PyPI or any
  Linux distribution.

  From the provided link (pyliblo_), clone the master branch of the source code
  repository, then merge both currently outstanding Pull Requests (#17 & #22) as
  we need the changes contained within both. Follow the instructions of the
  project's README to build and install. Depending on your chosen flavour of
  Linux, you may need to remove your distribution's package first.

python-zeroconf
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

Note: the plugin does not advertise the OSC/QLab service to the network. You
will need to manually enter your computer's IP address to whichever remote
control app you're using to connect.




.. _Linux Show Player: https://github.com/FrancescoCeruti/linux-show-player
.. _QLab Remote: https://qlab.app/qlab-remote/
.. _Figure53: http://figure53.com/
.. _Audio Toolbox: http://www.danielhiggott.com/the-audio-toolbox
.. _liblo: https://github.com/radarsat1/liblo
.. _pyliblo: https://github.com/dsacre/pyliblo
