from pathlib import Path
# Reuse the tested input/AT-SPI helpers without executing its test cases.
exec((Path(__file__).with_name('ui-test-dnd.py')).read_text().split('\ntry:\n wait(lambda:item')[0])
from PIL import ImageGrab,ImageStat,ImageChops
from gi.repository import GLib

def drain(seconds):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  while Gtk.events_pending():Gtk.main_iteration_do(False)
  time.sleep(.01)
def frame_ids():return run('search','--onlyvisible','--class','org.gnome.Nautilus').splitlines()
def location_windows():
 bus=Gio.bus_get_sync(Gio.BusType.SESSION,None)
 return bus.call_sync('org.freedesktop.FileManager1','/org/freedesktop/FileManager1','org.freedesktop.DBus.Properties','Get',GLib.Variant('(ss)',('org.freedesktop.FileManager1','OpenWindowsWithLocations')),None,Gio.DBusCallFlags.NONE,10000,None).unpack()[0]
def screenshot_image():return ImageGrab.grab()
def contrast(im,box):
 crop=im.crop(box).convert('RGB');white=__import__('PIL.Image',fromlist=['new']).new('RGB',crop.size,opacity_bg)
 return sum(ImageStat.Stat(ImageChops.difference(crop,white)).mean)
def drag_hold(start,end):
 run('mousemove',*start,'mousedown',1);time.sleep(.1)
 for step in range(1,16):
  run('mousemove',*[round(start[i]+(end[i]-start[i])*step/15) for i in range(2)]);time.sleep(.025)
 time.sleep(.2)
def finish_drag():run('mouseup',1);time.sleep(.3)
def pixel_border(im,color):
 pixels=list(im.getdata())
 if color=='blue':return sum(b>r+70 and b>g+50 and b>150 for r,g,b in pixels)
 return sum(g>r+50 and g>b+35 and g>100 for r,g,b in pixels)
try:
 wait(lambda:item('alpha.txt'),'initial files',45)
 wid=frame_ids()[0];run('windowsize',wid,900,650);run('windowmove',wid,0,0);run('windowfocus',wid);time.sleep(.5)
 click('alpha.txt');r=rect(tile('alpha.txt'));box=(r.x+25,r.y+8,r.x+r.width-25,r.y+70)
 before=screenshot_image();opacity_bg=before.getpixel((r.x+15,r.y+15));before.save(base/'cut-before.png');key('ctrl+x');time.sleep(.6)
 cut=screenshot_image();cut.save(base/'cut-after.png')
 ratio=contrast(cut,box)/contrast(before,box)
 assert .2<ratio<.7,('cut opacity contrast ratio',ratio)
 passed('cut file content becomes translucent while selection outline remains')
 Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text('replace cut clipboard',-1);drain(.8)
 restored=screenshot_image();assert contrast(restored,box)>contrast(before,box)*.9
 passed('clipboard replacement restores original opacity')
 # Full tile bounds define containment; mere overlap must not select left-to-right.
 r=rect(tile('alpha.txt'))
 start=(r.x-3,r.y+r.height+3);end=(r.x+r.width//2,r.y-3)
 drag_hold(start,end);im=screenshot_image();im.save(base/'window-selection.png')
 assert pixel_border(im,'blue')>pixel_border(before,'blue')+60,'missing blue selection rectangle'
 finish_drag();assert selected()==[],selected()
 passed('left-to-right partial overlap does not select; blue solid rectangle visible')
 drag_hold(start,(r.x+r.width+3,r.y-3));finish_drag();assert selected()==['alpha.txt'],selected()
 passed('left-to-right complete containment selects the file')
 drag_hold((r.x+r.width+3,r.y+r.height+3),end);im=screenshot_image();im.save(base/'crossing-selection.png')
 assert pixel_border(im,'green')>pixel_border(before,'green')+40,'missing green crossing rectangle'
 finish_drag();assert selected()==['alpha.txt'],selected()
 passed('right-to-left touching selects; green dashed rectangle visible')
 # Modified selections preserve or toggle the original selection.
 click('beta.txt');run('keydown','shift');drag_hold(start,(r.x+r.width+3,r.y-3));finish_drag();run('keyup','shift')
 assert set(selected())=={'alpha.txt','beta.txt'},selected()
 passed('Shift rectangle adds to existing selection')
 run('keydown','ctrl');drag_hold(start,(r.x+r.width+3,r.y-3));finish_drag();run('keyup','ctrl')
 assert selected()==['beta.txt'],selected()
 passed('Ctrl rectangle toggles only intersected selection')
 drag_hold(start,(r.x+r.width+3,r.y-3));run('key','Escape');time.sleep(.2);finish_drag()
 assert selected()==['beta.txt'],selected()
 passed('Escape cancels active rectangle without moving files')
 # Several windows, including a multi-tab window and a nontrivial back history.
 (folder/'destination'/'nested').mkdir(exist_ok=True)
 third=folder/'third';third.mkdir(exist_ok=True)
 fourth=folder/'fourth';fourth.mkdir(exist_ok=True)
 subprocess.run([sys.argv[1],'--new-window',str(folder/'destination')],check=True);time.sleep(.6)
 second=next(w for w in frame_ids() if w!=wid);run('windowfocus',second);go(folder/'destination'/'nested')
 subprocess.run([sys.argv[1],'--new-window',str(third)],check=True);time.sleep(.6)
 thirdwid=next(w for w in frame_ids() if w not in (wid,second));run('windowfocus',thirdwid);key('ctrl+t');go(fourth)
 assert len(location_windows())==3 and sum(map(len,location_windows().values()))==4,location_windows()
 # Put the current target in front, then middle-click only its blank file area.
 run('windowraise',wid);run('windowfocus',wid);run('mousemove',800,500,'click',2)
 wait(lambda:len(location_windows())==1,'merge windows')
 assert sum(map(len,location_windows().values()))==4,location_windows()
 expected={folder.as_uri(),(folder/'destination'/'nested').as_uri(),third.as_uri(),fourth.as_uri()}
 assert set(next(iter(location_windows().values())))==expected,location_windows()
 screenshot('merged-tabs.png');passed('middle-click background merges all windows and all existing tabs without duplication')
 tabs=lambda:[n for n in nodes() if n.getRoleName()=='page tab' and visible(n)]
 print('TABS',[(n.name,rect(n)) for n in tabs()],flush=True)
 nested=wait(lambda:next((n for n in tabs() if 'nested' in n.name),None),'nested tab')
 rr=rect(nested);run('mousemove',rr.x+rr.width//2,rr.y+rr.height//2,'click',1);time.sleep(.3);key('alt+Left')
 wait(lambda:(folder/'destination').as_uri() in next(iter(location_windows().values())),'history after merge')
 passed('merged tab retains its original back history')
 tab=wait(lambda:next((n for n in tabs() if 'fourth' in n.name),None),'fourth tab')
 rr=rect(tab);drag((rr.x+rr.width//2,rr.y+rr.height//2),(1250,850))
 wait(lambda:len(location_windows())==2,'detached tab window')
 assert sum(map(len,location_windows().values()))==4,location_windows()
 screenshot('detached-tab.png');passed('dragging a tab outside splits it into a separate window without losing tabs')
 run('windowraise',wid);run('windowfocus',wid);run('mousemove',800,500,'click',2)
 wait(lambda:len(location_windows())==1,'merge again');assert sum(map(len,location_windows().values()))==4
 passed('merge after detaching is repeatable and keeps all tabs')
 print('ALL REFINEMENT TESTS PASSED',flush=True)
except Exception:
 screenshot('refinements-failure.png');raise
finally:
 subprocess.run([sys.argv[1],'--quit'],capture_output=True,timeout=10)
