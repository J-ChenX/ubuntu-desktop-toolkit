import os
import pathlib
import subprocess
import sys
import time

import pyatspi
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, Gtk, Gio

base = pathlib.Path(__file__).resolve().parent
folder = base / 'navigation-fixture' / 'parent' / 'current'
folder.mkdir(parents=True, exist_ok=True)
(folder / 'renamed.txt').unlink(missing_ok=True)
(folder / 'rename-me.txt').write_text('keep this content')
(folder / 'other.txt').write_text('other')
(folder / 'child-folder').mkdir(exist_ok=True)
prefs = Gio.Settings.new('org.gnome.nautilus.preferences')
prefs.set_boolean('use-experimental-views', True)
Gio.Settings.sync()
pyatspi.Registry.getDesktop(0)
process = subprocess.Popen([sys.argv[1], '--new-window', str(folder)],
                           stdout=open(base / 'ui-app.log', 'w'), stderr=subprocess.STDOUT)

def walk(node):
    yield node
    for child in node:
        if child is not None:
            yield from walk(child)

def nodes():
    result = []
    for app in pyatspi.Registry.getDesktop(0):
        if app is not None and 'nautilus' in app.name.lower():
            result.extend(walk(app))
    return result

def showing(node):
    return node.getState().contains(pyatspi.STATE_SHOWING)

def wait_for(predicate, message):
    end = time.monotonic() + 45
    while time.monotonic() < end:
        try:
            result = predicate()
            if result:
                return result
        except (RuntimeError, LookupError):
            pass
        time.sleep(.2)
    for n in nodes():
        if showing(n):
            print(n.getRoleName(), repr(n.name), flush=True)
    raise AssertionError(message)

def button(name):
    return next((n for n in nodes() if n.name == name and n.getRoleName() == 'push button' and showing(n)), None)

def entry():
    return next((n for n in nodes() if n.getRoleName() in ('text', 'entry') and showing(n)
                 and n.getState().contains(pyatspi.STATE_EDITABLE)), None)

def click(node, mouse=1, right_edge=False):
    r = node.queryComponent().getExtents(pyatspi.DESKTOP_COORDS)
    x = r.x + (r.width - 12 if right_edge else r.width // 2)
    y = r.y + r.height // 2
    subprocess.run(['xdotool', 'mousemove', str(x), str(y), 'click', str(mouse)], check=True)
    time.sleep(.3)

def key(value):
    subprocess.run(['xdotool', 'key', '--clearmodifiers', value], check=True)
    time.sleep(.3)

def screenshot(name):
    root = Gdk.get_default_root_window()
    pix = Gdk.pixbuf_get_from_window(root, 0, 0, root.get_width(), root.get_height())
    pix.savev(str(base / name), 'png', [], [])


def item(name):
    return next((n for n in nodes() if n.name == name and showing(n)), None)

def settle():
    time.sleep(.85)

def point(x, y, count=1, modifier=None):
    if modifier:
        subprocess.run(['xdotool', 'keydown', modifier], check=True)
    subprocess.run(['xdotool', 'mousemove', str(x), str(y), 'click', '--repeat', str(count), '--delay', '100', '1'], check=True)
    if modifier:
        subprocess.run(['xdotool', 'keyup', modifier], check=True)
    time.sleep(.6)

def blank(count=1, modifier=None):
    frame = next(n for n in nodes() if n.getRoleName() == 'frame' and showing(n))
    r = frame.queryComponent().getExtents(pyatspi.DESKTOP_COORDS)
    point(r.x + r.width - 110, r.y + r.height - 140, count, modifier)

def path_value():
    key('ctrl+l')
    field = wait_for(entry, 'Location entry missing')
    value = field.queryText().getText(0,-1)
    key('Escape')
    return value

def go(path):
    key('ctrl+l')
    wait_for(entry, 'No entry for navigation').queryEditableText().setTextContents(str(path))
    key('Return')
    time.sleep(.7)

def check_path(expected):
    actual = path_value()
    assert Gio.File.new_for_commandline_arg(actual).equal(Gio.File.new_for_commandline_arg(str(expected))), (actual, str(expected))

try:
    wait_for(lambda: button('current'), 'Initial breadcrumb missing')
    subprocess.run(['xdotool', 'search', '--onlyvisible', '--class', 'org.gnome.Nautilus', 'windowsize', '1100', '800'], check=True)
    time.sleep(.5)
    for mode, shortcut in [('grid','ctrl+2'), ('list','ctrl+1')]:
        key(shortcut)
        go(folder)
        click(wait_for(lambda: button('current'), 'Current missing'))
        wait_for(entry, 'Address click must enter edit mode')
        blank()
        assert entry() is None, mode + ': blank click must hide location entry'
        assert button('current') is not None
        check_path(folder)
        print('PASS', mode, 'address editing -> blank single click restores breadcrumbs without navigation', flush=True)

        key('ctrl+l')
        wait_for(entry, 'Missing field').queryEditableText().setTextContents('/not/a/real/path')
        blank()
        assert entry() is None
        check_path(folder)
        print('PASS', mode, 'unsubmitted address is cancelled on blank click', flush=True)

        blank(2)
        check_path(folder.parent)
        print('PASS', mode, 'blank double click goes to parent', flush=True)
        go(folder)
        key('ctrl+l')
        blank(2)
        assert entry() is None
        check_path(folder.parent)
        print('PASS', mode, 'double click while editing also navigates up', flush=True)

        go(folder)
        key('ctrl+a')
        blank(2)
        check_path(folder.parent)
        print('PASS', mode, 'selection does not prevent blank double click', flush=True)

        go(folder)
        for modifier in ('ctrl', 'shift', 'alt'):
            blank(2, modifier)
            check_path(folder)
        print('PASS', mode, 'modified double clicks do not navigate', flush=True)

        # The first click moves out and back while held: it is a drag, not a click.
        frame = next(n for n in nodes() if n.getRoleName() == 'frame' and showing(n))
        r=frame.queryComponent().getExtents(pyatspi.DESKTOP_COORDS)
        x,y=r.x+r.width-110,r.y+r.height-140
        subprocess.run(['xdotool','mousemove',str(x),str(y),'mousedown','1','mousemove',str(x-150),str(y-100),'sleep','.1','mouseup','1'],check=True)
        point(x-150,y-100)
        check_path(folder)
        print('PASS', mode, 'rubber-band selection does not navigate',flush=True)

        go(folder)
        target=wait_for(lambda:item('child-folder'), 'Child not visible')
        r=target.queryComponent().getExtents(pyatspi.DESKTOP_COORDS)
        point(r.x+r.width//2,r.y+r.height//2,2)
        check_path(folder/'child-folder')
        print('PASS',mode,'double clicking a folder still opens it',flush=True)
        blank(2)
        check_path(folder)
        print('PASS',mode,'empty folder double click goes up',flush=True)

        prefs.set_string('click-policy', 'single'); Gio.Settings.sync(); time.sleep(.3)
        blank(2)
        check_path(folder.parent)
        prefs.set_string('click-policy', 'double'); Gio.Settings.sync()
        print('PASS',mode,'background double click also works in single-click-open mode',flush=True)

    key('ctrl+2')
    go('/')
    key('ctrl+minus'); key('ctrl+minus')
    blank(2)
    check_path('/')
    print('PASS filesystem root remains at root',flush=True)
    go('recent:///')
    blank(2)
    from gi.repository import GLib
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    locations = bus.call_sync('org.freedesktop.FileManager1', '/org/freedesktop/FileManager1',
        'org.freedesktop.DBus.Properties', 'Get', GLib.Variant('(ss)',
        ('org.freedesktop.FileManager1', 'OpenLocations')), None, Gio.DBusCallFlags.NONE, 5000, None).unpack()[0]
    assert 'recent:///' in locations, locations
    print('PASS recent view has no parent navigation',flush=True)
    screenshot('navigation-final.png')
finally:
    subprocess.run([sys.argv[1], '--quit'], timeout=10)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.terminate()
