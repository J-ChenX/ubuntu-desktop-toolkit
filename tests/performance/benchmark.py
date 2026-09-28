import os,time,subprocess,tempfile,json,math
from pathlib import Path
import gi
gi.require_version('Gio','2.0')
from gi.repository import Gio
prefs=Gio.Settings.new('org.gnome.nautilus.preferences');prefs.set_boolean('use-experimental-views',True);Gio.Settings.sync()
def x(*args):subprocess.run(['xdotool',*map(str,args)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def snap(pid):
 p=Path('/proc',str(pid));s=(p/'stat').read_text().rsplit(')',1)[1].split();m=dict(l.split(':',1) for l in (p/'smaps_rollup').read_text().splitlines() if ':' in l)
 return (int(s[11])+int(s[12]))/os.sysconf('SC_CLK_TCK'),int(m['Pss'].split()[0])
rows=[]
with tempfile.TemporaryDirectory(prefix='desktop-perf-fixture-') as td:
 for count in [5000]:
  folder=Path(td)/str(count);folder.mkdir()
  for i in range(count):(folder/f'item-{i:05}.txt').touch()
  proc=subprocess.Popen([os.environ.get('BENCH_BINARY','/usr/bin/nautilus'),'--new-window',str(folder)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  try:
   wid=''
   for _ in range(100):
    ids=subprocess.run(['xdotool','search','--onlyvisible','--class','org.gnome.Nautilus'],capture_output=True,text=True).stdout.split()
    if ids:wid=ids[0];break
    time.sleep(.1)
   if not wid:raise RuntimeError('no test window')
   x('windowsize',wid,1000,700);x('windowmove',wid,0,0);x('windowfocus',wid)
   time.sleep(6)
   for _ in range(12):
    warm=snap(proc.pid);time.sleep(2)
    if snap(proc.pid)[0]-warm[0] < .02:break
   a=snap(proc.pid);start=time.monotonic();time.sleep(3);b=snap(proc.pid);idle=(b[0]-a[0])/(time.monotonic()-start)*100
   x('mousemove',205,580,'mousedown',1)
   a=snap(proc.pid);start=time.monotonic()
   for i in range(600):
    x('mousemove',600+int(140*math.sin(i*.15)),180+int(60*math.cos(i*.15)))
    time.sleep(.001)
   from PIL import ImageGrab
   ImageGrab.grab().save(os.environ['PERF_OUTPUT']+'.png')
   x('mouseup',1);time.sleep(2);b=snap(proc.pid);elapsed=time.monotonic()-start
   rows.append({'file_count':count,'idle_cpu_percent_one_core':round(idle,2),'drag_and_settle_seconds':round(elapsed,2),'drag_and_settle_cpu_seconds':round(b[0]-a[0],3),'drag_and_settle_cpu_percent_one_core':round((b[0]-a[0])/elapsed*100,2),'pss_before_mib':round(a[1]/1024,2),'pss_after_mib':round(b[1]/1024,2)})
   print(json.dumps(rows[-1]),flush=True)
  finally:
   subprocess.run([os.environ.get('BENCH_BINARY','/usr/bin/nautilus'),'--quit'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   try:proc.wait(timeout=8)
   except subprocess.TimeoutExpired:proc.terminate();proc.wait(timeout=5)
Path(os.environ['PERF_OUTPUT']).write_text(json.dumps({'method':'Xvfb, GIO local, 600 scripted pointer moves at 1ms requested interval plus 2s settle; includes UI work, not frame-latency measurement; no stock baseline','results':rows},indent=2))
