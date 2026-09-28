#!/usr/bin/python3
"""Start Terminator with a dark GTK theme and matching window decorations."""
import os
import runpy
import sys
import gi

os.environ['GTK_THEME'] = 'Yaru:dark'
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, GLib, Gdk

Gdk.set_program_class('Terminator')

settings = Gtk.Settings.get_default()
if settings is not None:
    settings.set_property('gtk-application-prefer-dark-theme', True)
GLib.set_prgname('terminator')
sys.argv[0] = '/usr/bin/terminator'
runpy.run_path('/usr/bin/terminator', run_name='__main__')
