import os, sys, time, tempfile, subprocess, gc
from pathlib import Path
from PIL import ImageGrab
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
base = Path(__file__).resolve().parent
xdotool = str(Path.home()/'.local/share/nautilus-navigation-20260922/test-tools/xdotool')
fixture = tempfile.TemporaryDirectory(prefix='gtk-click-path-')
folder = Path(fixture.name)/'parent'/'current'
folder.mkdir(parents=True)
(folder/'sample.txt').write_text('fixture')

def drain(seconds=.15):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        while Gtk.events_pending(): Gtk.main_iteration_do(False)
        time.sleep(.005)

def walk(w):
    yield w
    if isinstance(w,Gtk.Container):
        for c in w.get_children(): yield from walk(c)

def named(dialog,name):
    return next(w for w in walk(dialog) if w.get_name()==name)

def template(chooser,name):
    return chooser.get_template_child(Gtk.FileChooserWidget,name)

def click(w, button=1, position=None):
    win=w.get_toplevel()
    x,y=w.translate_coordinates(win,0,0)
    _,ox,oy=win.get_window().get_origin()
    width,height=w.get_allocated_width(),w.get_allocated_height()
    dx,dy=position or (width//2,height//2)
    subprocess.run([xdotool,'mousemove',str(ox+x+dx),str(oy+y+dy),'click',str(button)],check=True,timeout=5)
    drain(.3)

def key(combo):
    subprocess.run([xdotool,'key','--clearmodifiers',combo],check=True,timeout=5)
    drain()

def create(action):
    d=Gtk.FileChooserDialog(title='GTK click-path test',action=action)
    d.add_buttons('Cancel',Gtk.ResponseType.CANCEL,'Select',Gtk.ResponseType.ACCEPT)
    d.set_default_size(1000,650)
    d.set_current_folder(str(folder))
    d.show_all(); drain(.6)
    if "--dynamic" in sys.argv:
        Gtk.Settings.get_default().set_property("gtk-modules", str(base/"libgtk-filechooser-click-path.so"))
        drain()
    c=next(w for w in walk(d) if isinstance(w,Gtk.FileChooserWidget))
    stack=template(c,'browse_header_stack')
    if stack.get_visible_child_name()=='location':
        click(named(d,'click-path-back'))
    return d,c,stack

def check(value,message):
    assert value,message
    print('PASS',message,flush=True)

def current_button(c):
    return next(b for b in template(c,'browse_path_bar').get_children()
                if isinstance(b,Gtk.ToggleButton) and b.get_active())

d,c,stack=create(Gtk.FileChooserAction.OPEN)
check(stack.get_visible_child_name()=='pathbar','open starts with breadcrumbs')
click(current_button(c))
check(stack.get_visible_child_name()=='location','click current directory opens location entry')
entry=next(w for w in walk(template(c,'location_entry_box')) if isinstance(w,Gtk.Entry))
check(entry.has_focus(),'location entry has focus')
click(named(d,'click-path-back'))
check(stack.get_visible_child_name()=='pathbar','back button restores breadcrumbs')
blank=template(c,'browse_path_bar')
click(blank,position=(blank.get_allocated_width()-8,blank.get_allocated_height()//2))
check(stack.get_visible_child_name()=='location','click empty pathbar area opens location entry')
key('ctrl+l')
check(stack.get_visible_child_name()=='pathbar','Ctrl+L restores breadcrumbs')
key('ctrl+l')
check(stack.get_visible_child_name()=='location','Ctrl+L still opens entry')
click(named(d,'click-path-back'))
click(current_button(c),button=3)
check(stack.get_visible_child_name()=='pathbar','right click does not switch modes')
# Ancestor button must navigate without entering edit mode.
parent_button=next(b for b in template(c,'browse_path_bar').get_children()
                   if isinstance(b,Gtk.ToggleButton) and any(isinstance(w,Gtk.Label) and w.get_text()=='parent' for w in walk(b)))
click(parent_button); drain(.4)
check(c.get_current_folder()==str(folder.parent) and stack.get_visible_child_name()=='pathbar','ancestor click navigates and retains breadcrumbs')
click(current_button(c))
check(stack.get_visible_child_name()=='location','current ancestor also switches on a second click')
entry=next(w for w in walk(template(c,'location_entry_box')) if isinstance(w,Gtk.Entry))
entry.set_text(str(folder)+'/'); key('Return'); drain(.4)
check(c.get_current_folder()==str(folder),'typed directory navigation still works')
if stack.get_visible_child_name()=='location': click(named(d,'click-path-back'))
# Capture actual rendered widget.
ImageGrab.grab().save(base/"test-breadcrumbs.png")
click(current_button(c))
ImageGrab.grab().save(base/"test-location.png")
d.destroy();d=c=stack=entry=blank=parent_button=None;gc.collect();drain()

d,c,stack=create(Gtk.FileChooserAction.SAVE)
d.set_current_name('unchanged.txt');drain()
click(current_button(c));drain(.3)
check(stack.get_visible_child_name()=='pathbar' and d.get_current_name()=='unchanged.txt','save dialog keeps filename and existing path behavior')
d.destroy();d=c=stack=entry=blank=parent_button=None;gc.collect();drain()

d,c,stack=create(Gtk.FileChooserAction.SELECT_FOLDER)
click(current_button(c))
check(stack.get_visible_child_name()=='location','folder picker supports click to edit')
click(named(d,'click-path-back'))
check(stack.get_visible_child_name()=='pathbar','folder picker supports click to return')
d.destroy();d=c=stack=entry=blank=parent_button=None;gc.collect();drain()
for _ in range(10):
    d,c,stack=create(Gtk.FileChooserAction.OPEN)
    click(current_button(c));d.destroy();d=c=stack=None;gc.collect();drain(.2)
check(True,'repeated dialog creation and destruction')
fixture.cleanup()
