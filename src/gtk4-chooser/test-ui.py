import ctypes,gc,os,subprocess,tempfile,time
from pathlib import Path
import gi
gi.require_version('Gtk','4.0');gi.require_version('GdkX11','4.0')
from gi.repository import Gtk,Gio,GLib,GdkX11
from PIL import ImageGrab
base=Path(__file__).resolve().parent
xdotool=str(Path.home()/'.local/share/nautilus-navigation-20260922/test-tools/xdotool')
realize=ctypes.CDLL(None).gtk_widget_realize
realize.argtypes=[ctypes.c_void_p]
fixture=tempfile.TemporaryDirectory(prefix='portal-click-')
folder=Path(fixture.name)/'parent'/'当前 目录';folder.mkdir(parents=True)
(folder/'sample.txt').write_text('local fixture only')
def drain(seconds=.35):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        while GLib.MainContext.default().pending():GLib.MainContext.default().iteration(False)
        time.sleep(.005)
def walk(w):
    yield w
    child=w.get_first_child()
    while child:
        yield from walk(child);child=child.get_next_sibling()
def part(c,name):return c.get_template_child(Gtk.FileChooserWidget,name)
def click(w,button=1,position=None):
    root=w.get_root();ok,bounds=w.compute_bounds(root);assert ok
    geometry=dict(line.split('=',1) for line in subprocess.check_output([xdotool,'getwindowgeometry','--shell',str(root.get_surface().get_xid())],text=True).splitlines())
    x,y=position or (w.get_width()/2,w.get_height()/2)
    x+=int(geometry['X']);y+=int(geometry['Y'])
    subprocess.run([xdotool,'mousemove',str(round(bounds.get_x()+x)),str(round(bounds.get_y()+y)),'click',str(button)],check=True,timeout=5)
    drain()
def key(k):
    subprocess.run([xdotool,'key','--clearmodifiers',k],check=True,timeout=5);drain()
def back(d):return next(w for w in walk(d) if w.get_name()=='portal-click-back')
def current(c):return next(w for w in walk(part(c,'browse_path_bar')) if isinstance(w,Gtk.ToggleButton) and w.get_active())
def check(ok,msg):assert ok,msg;print('PASS',msg,flush=True)
def check_address(c,expected,label):
    entry=next(w for w in walk(part(c,'location_entry_box')) if isinstance(w,Gtk.Editable))
    check(entry.get_text()==str(expected),label+' shows current full folder path')
    bounds=entry.get_selection_bounds()
    check(bounds==(0,len(str(expected))),label+' selects the entire Unicode path')
    focus=entry.get_root().get_focus()
    check(focus==entry or focus.is_ancestor(entry),label+' focuses the location editor')

def create(action):
    d=Gtk.FileChooserDialog(title='GTK4 Portal click test',action=action)
    d.add_buttons('Cancel',Gtk.ResponseType.CANCEL,'Select',Gtk.ResponseType.ACCEPT)
    d.set_default_size(1000,650);d.set_current_folder(Gio.File.new_for_path(str(folder)))
    realize(hash(d));d.present();drain(.6)
    subprocess.run([xdotool,'windowmove',str(d.get_surface().get_xid()),'50','50','windowfocus',str(d.get_surface().get_xid())],check=True,timeout=5)
    c=next(w for w in walk(d) if isinstance(w,Gtk.FileChooserWidget));stack=part(c,'browse_header_stack')
    if stack.get_visible_child_name()=='location':click(back(d))
    return d,c,stack

d,c,stack=create(Gtk.FileChooserAction.OPEN)
check(stack.get_visible_child_name()=='pathbar','GTK4 chooser initialized with patch')
d.set_file(Gio.File.new_for_path(str(folder/'sample.txt')));drain()
click(current(c));check(stack.get_visible_child_name()=='location','current breadcrumb opens location')
check_address(c,folder,'current breadcrumb with a selected file')
click(back(d));check(stack.get_visible_child_name()=='pathbar','back arrow restores breadcrumbs')
bar=part(c,'browse_path_bar');click(bar,position=(bar.get_width()-8,bar.get_height()/2))
check(stack.get_visible_child_name()=='location','empty area opens location')
check_address(c,folder,'blank-area click')
click(back(d));check(stack.get_visible_child_name()=='pathbar','back returns after blank-area editing')
# Background dismissal cancels unsubmitted text and leaves file interactions intact.
click(current(c))
entry=next(w for w in walk(part(c,'location_entry_box')) if isinstance(w,Gtk.Editable))
entry.set_text('/unsubmitted/location/that/does/not/exist');drain()
tree=part(c,'browse_files_tree_view')
click(tree,position=(tree.get_width()/2,tree.get_height()-25))
check(stack.get_visible_child_name()=='pathbar','file-list blank click restores breadcrumbs')
check(c.get_current_folder().get_path()==str(folder),'background click cancels unsubmitted navigation')
check(d.get_focus()==tree or d.get_focus().is_ancestor(tree),'background click focuses the file list')
click(current(c));check_address(c,folder,'reopening after background dismissal')
# A row is not background: selection must still work without swallowing clicks.
rect=tree.get_background_area(Gtk.TreePath.new_from_indices([0]),None)
x,y=tree.convert_bin_window_to_widget_coords(30,rect.y+rect.height//2)
click(tree,position=(x,y))
check(stack.get_visible_child_name()=='location','file-row click does not count as background')
check(c.get_file().get_path()==str(folder/'sample.txt'),'file-row selection still works')
# Modified background clicks preserve the edit state.
subprocess.run([xdotool,'keydown','ctrl'],check=True)
try:click(tree,position=(tree.get_width()/2,tree.get_height()-25))
finally:subprocess.run([xdotool,'keyup','ctrl'],check=True)
check(stack.get_visible_child_name()=='location','Ctrl-click background does not cancel editing')
click(tree,position=(tree.get_width()/2,tree.get_height()-25))
check(stack.get_visible_child_name()=='pathbar','plain background click still dismisses after row selection')
key('ctrl+l');check(stack.get_visible_child_name()=='location','Ctrl+L opens location')
click(back(d));click(current(c),3);check(stack.get_visible_child_name()=='pathbar','right click does not toggle')
parent=next(w for w in walk(bar) if isinstance(w,Gtk.ToggleButton) and any(isinstance(t,Gtk.Label) and t.get_text()=='parent' for t in walk(w)))
click(parent);check(c.get_current_folder().get_path()==str(folder.parent) and stack.get_visible_child_name()=='pathbar','ancestor navigates without editing')
click(current(c));check(stack.get_visible_child_name()=='location','second click edits current ancestor')
check_address(c,folder.parent,'ancestor after navigation')
entry=next(w for w in walk(part(c,'location_entry_box')) if isinstance(w,Gtk.Editable))
entry.set_text(str(folder)+'/');key('Return');drain()
check(c.get_current_folder().get_path()==str(folder),'typed folder navigation')
if stack.get_visible_child_name()=='location':click(back(d))
ImageGrab.grab().save(base/'gtk4-breadcrumbs.png')
click(current(c));ImageGrab.grab().save(base/'gtk4-location.png')
d.destroy();d=c=stack=bar=parent=entry=None;gc.collect();drain()
d,c,stack=create(Gtk.FileChooserAction.SAVE);d.set_current_name('preserved.txt');drain()
click(current(c));check(d.get_current_name()=='preserved.txt' and stack.get_visible_child_name()=='pathbar','save filename preserved')
d.destroy();d=c=stack=None;gc.collect();drain()
d,c,stack=create(Gtk.FileChooserAction.SELECT_FOLDER);click(current(c))
check(stack.get_visible_child_name()=='location','folder picker click-to-edit')
check_address(c,folder,'folder picker')
click(back(d));check(stack.get_visible_child_name()=='pathbar','folder picker back arrow')
d.destroy();d=c=stack=None;gc.collect();drain()
empty=folder/'empty';empty.mkdir()
d,c,stack=create(Gtk.FileChooserAction.OPEN);d.set_current_folder(Gio.File.new_for_path(str(empty)));drain(.6)
click(current(c));tree=part(c,'browse_files_tree_view')
click(tree,position=(tree.get_width()/2,tree.get_height()/2))
check(stack.get_visible_child_name()=='pathbar' and c.get_current_folder().get_path()==str(empty),'empty directory background returns without navigation')
d.destroy();d=c=stack=tree=entry=None;gc.collect();drain()
for _ in range(8):
    d,c,stack=create(Gtk.FileChooserAction.OPEN);click(current(c));d.destroy();d=c=stack=None;gc.collect();drain()
check(True,'repeated create/close after editing')
fixture.cleanup()
