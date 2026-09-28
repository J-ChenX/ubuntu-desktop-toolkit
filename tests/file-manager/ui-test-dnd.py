import os,sys,time,subprocess,pathlib,json,shutil
import pyatspi
import gi
gi.require_version('Gtk','3.0');gi.require_version('Gdk','3.0')
from gi.repository import Gio,Gdk,Gtk
base=pathlib.Path(__file__).resolve().parent
folder=base/'dnd-fixture'
if folder.exists():shutil.rmtree(folder)
folder.mkdir()
(folder/'destination').mkdir()
for name in ['alpha.txt','beta.txt','rename-me.txt']:(folder/name).write_text(name+' content\n')
prefs=Gio.Settings.new('org.gnome.nautilus.preferences')
prefs.set_boolean('use-experimental-views',True)
prefs.set_string('default-folder-viewer','icon-view')
Gio.Settings.sync()
pyatspi.Registry.getDesktop(0)
process=subprocess.Popen([sys.argv[1],'--new-window',str(folder)],stdout=open(base/'dnd-app.log','w'),stderr=subprocess.STDOUT)
receiver=None
browser=None

def run(*args):return subprocess.run(['xdotool',*map(str,args)],check=True,capture_output=True,text=True).stdout

def walk(n):
 yield n
 for c in n:
  if c:yield from walk(c)
def nodes():
 return [n for a in pyatspi.Registry.getDesktop(0) if a and 'nautilus' in a.name.lower() for n in walk(a)]
def visible(n):return n.getState().contains(pyatspi.STATE_SHOWING)
def wait(fn,label,seconds=12):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  try:
   value=fn()
   if value:return value
  except (RuntimeError,LookupError):pass
  time.sleep(.15)
 raise AssertionError(label)
def item(name):return next((n for n in nodes() if n.name==name and visible(n) and n.getRoleName() not in ('push button','frame')),None)
def tile(name):
 n=wait(lambda:item(name),'Missing '+name)
 while n.parent and n.getRoleName() not in ('list item','canvas'):
  if n.parent.getRoleName() in ('panel','viewport'):break
  n=n.parent
 return n

def rect(n):return n.queryComponent().getExtents(pyatspi.DESKTOP_COORDS)
def xy(name,padding=False):
 r=rect(tile(name));return (r.x+6 if padding else r.x+r.width//2,r.y+6 if padding else r.y+r.height//3)
def key(k):run('key','--clearmodifiers',k);time.sleep(.25)
def click(name,padding=False):run('mousemove',*xy(name,padding),'click',1);time.sleep(.25)
def selected():
 clip=Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
 clip.set_text('',-1)
 key('ctrl+shift+c')
 return [pathlib.Path(p).name for p in (clip.wait_for_text() or '').splitlines()]

def screenshot(name):
 root=Gdk.get_default_root_window();Gdk.pixbuf_get_from_window(root,0,0,root.get_width(),root.get_height()).savev(str(base/name),'png',[],[])
def drag(start,end,modifier=None,cancel=False):
 if modifier:run('keydown',modifier)
 run('mousemove',*start,'mousedown',1)
 time.sleep(.12)
 for step in range(1,16):
  pos=[round(start[i]+(end[i]-start[i])*step/15) for i in range(2)]
  run('mousemove',*pos);time.sleep(.035)
 time.sleep(.3)
 if cancel:run('key','Escape');time.sleep(.2)
 run('mouseup',1)
 if modifier:run('keyup',modifier)
 time.sleep(.5)

def go(path):
 key('ctrl+l')
 entry=wait(lambda:next((n for n in nodes() if n.getRoleName() in ('text','entry') and visible(n) and n.getState().contains(pyatspi.STATE_EDITABLE)),None),'location entry')
 entry.queryEditableText().setTextContents(str(path));key('Return');time.sleep(.5)

def passed(s):print('PASS',s,flush=True)
try:
 wait(lambda:item('alpha.txt'),'initial files',45)
 wid=run('search','--onlyvisible','--class','org.gnome.Nautilus').splitlines()[0]
 run('windowsize',wid,900,650);run('windowmove',wid,0,0);run('windowfocus',wid)
 time.sleep(.5)
 for name in ['alpha.txt','destination']:print('TILE',name,tile(name).getRoleName(),rect(tile(name)),flush=True)
 click('alpha.txt',True)
 assert 'alpha.txt' in selected(),selected()
 screenshot('selected-style.png')
 (base/'received.json').unlink(missing_ok=True)
 receiver=subprocess.Popen(['/usr/bin/python3',str(base/'receiver.py'),str(base/'received.json')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 time.sleep(.6)
 run('windowfocus',wid)
 # Starting in the padding of an already selected tile must export a file,
 # not rubberband. A generic GTK receiver validates external URI transfer.
 drag(xy('alpha.txt',True),(1120,200))
 wait(lambda:(base/'received.json').exists(),'external file drop')
 assert json.loads((base/'received.json').read_text())==[(folder/'alpha.txt').as_uri()]
 assert (folder/'alpha.txt').exists()
 passed('whole selected tile padding -> external application URI, original retained')
 # Escape must leave files untouched and must not fire slow-click rename.
 drag(xy('alpha.txt'),(650,460),cancel=True)
 time.sleep(.8)
 assert (folder/'alpha.txt').exists()
 assert not any(n.getRoleName()=='dialog' and visible(n) for n in nodes())
 passed('Escape cancels drag without moving or renaming')
 # File-to-folder drop uses the existing file operation engine.
 drag(xy('alpha.txt',True),xy('destination'))
 wait(lambda:(folder/'destination'/'alpha.txt').exists() and not (folder/'alpha.txt').exists(),'move into folder')
 passed('file tile -> folder tile moves file')
 key('ctrl+z')
 wait(lambda:(folder/'alpha.txt').exists(),'undo move')
 passed('undo restores moved file')
 # Select a second file with Ctrl and drag the whole selection.
 click('alpha.txt');run('keydown','ctrl');click('beta.txt');run('keyup','ctrl');time.sleep(.15)
 print('MULTI',selected(),flush=True)
 (base/'received.json').unlink()
 drag(xy('alpha.txt',True),(1120,200))
 wait(lambda:(base/'received.json').exists(),'multi file export')
 assert set(json.loads((base/'received.json').read_text()))=={(folder/'alpha.txt').as_uri(),(folder/'beta.txt').as_uri()}
 passed('multi-selection exports both files')
 # Reset selection; explicit Ctrl-drag copies instead of moving.
 go(folder)
 click('beta.txt')
 drag(xy('beta.txt'),xy('destination'),modifier='ctrl')
 wait(lambda:(folder/'destination'/'beta.txt').exists(),'Ctrl-copy')
 assert (folder/'beta.txt').exists(),'Ctrl drag incorrectly moved source'
 passed('Ctrl-drag copies and keeps source')
 # Blank-area rubberband must still select.
 run('mousemove',700,500,'click',1);time.sleep(.2)
 drag((800,195),(210,65))
 assert len(selected())>=2,selected()
 passed('background rubberband selection retained')
 # Drag into another window's empty content area.
 receiver.terminate();receiver.wait();receiver=None
 subprocess.run([sys.argv[1],'--new-window',str(folder/'destination')],check=True)
 destwid=wait(lambda:subprocess.run(['xdotool','search','--onlyvisible','--name','^destination$'],capture_output=True,text=True).stdout.strip(),'second file window').splitlines()[0]
 time.sleep(.5)
 print('WINDOWS',wid,destwid,run('getwindowname',wid),run('getwindowname',destwid),flush=True)
 run('windowsize',destwid,560,650);run('windowmove',destwid,930,0);run('windowfocus',wid)
 run('mousemove',800,550,'click',1);time.sleep(.2)
 click('alpha.txt')
 drag(xy('alpha.txt',True),(1250,450))
 wait(lambda:(folder/'destination'/'alpha.txt').exists() and not (folder/'alpha.txt').exists(),'cross-window move')
 passed('cross-window drop on background moves file')
 run('windowfocus',destwid);key('ctrl+w');run('windowfocus',wid);key('ctrl+z')
 wait(lambda:(folder/'alpha.txt').exists(),'undo cross-window move')
 # A no-op same-folder drop must not open an error or move data.
 click('alpha.txt');drag(xy('alpha.txt'),(700,450))
 assert (folder/'alpha.txt').exists()
 assert not any(n.getRoleName() in ('dialog','alert') and visible(n) for n in nodes())
 passed('same-directory no-op drop is rejected without an error dialog')

 # Chromium must see real File objects with readable bytes, not just text URLs.
 browser=subprocess.Popen(['google-chrome','--no-first-run','--no-default-browser-check',
  '--disable-background-networking','--disable-sync','--disable-extensions',
  '--user-data-dir='+str(base/'browser-profile'),'--window-size=430,650','--window-position=1000,0',
  '--app='+str((base/'browser-drop.html').as_uri())],stdout=open(base/'browser.log','w'),stderr=subprocess.STDOUT)
 bid=wait(lambda:subprocess.run(['xdotool','search','--onlyvisible','--name','DnD Browser Test'],capture_output=True,text=True).stdout.strip(),'browser window',20).splitlines()[0]
 run('windowmove',bid,1000,0);run('windowsize',bid,430,650);run('windowfocus',wid)
 run('mousemove',800,550,'click',1);time.sleep(.2);click('alpha.txt')
 drag(xy('alpha.txt',True),(1150,220))
 title=wait(lambda:(t if 'RECEIVED:' in t else None) if (t:=run('getwindowname',bid)) else None,'browser file receipt')
 assert 'alpha.txt content' in title,title
 passed('Chromium receives a File object with original filename and readable content')

 screenshot('dnd-after.png')
 print('ALL DND TESTS PASSED',flush=True)
except Exception:
 screenshot('dnd-failure.png')
 for n in nodes():
  if visible(n):print(n.getRoleName(),repr(n.name),rect(n),flush=True)
 raise
finally:
 if browser:browser.terminate()
 if receiver:receiver.terminate()
 process.terminate()
