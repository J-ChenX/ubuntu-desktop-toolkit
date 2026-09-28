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
folder = base / 'rename-fixture' / 'parent' / 'current'
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

try:
    target=wait_for(lambda:item('rename-me.txt'), 'File not shown')
    click(target)
    settle()
    assert entry() is None, 'First click triggered rename'
    print('PASS: first filename click only selects', flush=True)

    click(wait_for(lambda:item('rename-me.txt'), 'Missing selected file'))
    field=wait_for(entry,'Second filename click did not trigger rename')
    assert field.queryText().getText(0,-1)=='rename-me.txt'
    screenshot('rename-active.png')
    key('ctrl+a')
    subprocess.run(['xdotool','type','--clearmodifiers','renamed.txt'],check=True)
    key('Return')
    wait_for(lambda:(folder/'renamed.txt').exists(),'Rename did not complete')
    assert (folder/'renamed.txt').read_text()=='keep this content'
    print('PASS: slow second filename click opens rename and Enter renames correctly',flush=True)

    # A click on the icon area of the selected tile must not rename.
    label=wait_for(lambda:item('renamed.txt'),'Missing renamed item')
    r=label.queryComponent().getExtents(pyatspi.DESKTOP_COORDS)
    subprocess.run(['xdotool','mousemove',str(r.x+r.width//2),str(r.y-30),'click','1'],check=True)
    settle()
    assert entry() is None,'Click on icon triggered rename'
    print('PASS: selected icon click does not rename',flush=True)

    target=wait_for(lambda:item('renamed.txt'),'Missing renamed item')
    r=target.queryComponent().getExtents(pyatspi.DESKTOP_COORDS)
    x=r.x+r.width//2; y=r.y+r.height//2
    subprocess.run(['xdotool','mousemove',str(x),str(y),'mousedown','1','mousemove',str(x+30),str(y+10),'sleep','0.15','mouseup','1'],check=True)
    settle()
    assert entry() is None,'Dragging a selected label triggered rename'
    assert (folder/'renamed.txt').exists()
    print('PASS: dragging selected filename does not rename',flush=True)
    key('F2')
    wait_for(entry,'F2 no longer opens rename')
    key('Escape')
    print('PASS: F2 shortcut and Escape dismissal preserved',flush=True)

    key('ctrl+a')
    target=wait_for(lambda:item('renamed.txt'),'Missing renamed item')
    click(target)
    settle()
    assert entry() is None,'Multi-selection triggered rename'
    print('PASS: clicking within multi-selection does not start rename',flush=True)

    # A pending rename is canceled by Escape or a different selection.
    click(wait_for(lambda:item('renamed.txt'),'Missing renamed item'))
    key('Escape')
    settle()
    assert entry() is None,'Escape did not cancel pending rename'
    click(wait_for(lambda:item('renamed.txt'),'Missing renamed item'))
    click(wait_for(lambda:item('other.txt'),'Missing other item'))
    settle()
    assert entry() is None,'Selection change did not cancel rename'
    print('PASS: keyboard input and selection changes cancel pending rename',flush=True)

    target=wait_for(lambda:item('child-folder'),'Missing child folder')
    click(target)
    settle()
    r=target.queryComponent().getExtents(pyatspi.DESKTOP_COORDS)
    subprocess.run(['xdotool','mousemove',str(r.x+r.width//2),str(r.y+r.height//2),'click','--repeat','2','--delay','90','1'],check=True)
    settle()
    assert entry() is None,'Double click triggered rename'
    key('ctrl+l')
    field=wait_for(entry,'Location entry missing')
    assert pathlib.Path(field.queryText().getText(0,-1))==folder/'child-folder'
    print('PASS: double-click on selected folder name opens folder',flush=True)
finally:
    subprocess.run([sys.argv[1], '--quit'], timeout=10)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.terminate()
