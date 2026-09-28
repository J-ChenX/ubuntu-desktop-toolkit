#!/usr/bin/python3
"""Clean only this user's processes carrying an exact private test runtime tag."""
import os,signal,sys,time
from pathlib import Path
runtime=Path(sys.argv[1]).resolve()
if not str(runtime).startswith(('/tmp/nautilus-refine.','/tmp/desktop-perf.','/tmp/udt-test.')) or runtime.stat().st_uid!=os.getuid():raise SystemExit('Refusing non-test runtime')
ancestors=set();pid=os.getpid()
while pid>1:
 ancestors.add(pid)
 try:pid=int(Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[1])
 except (OSError,ValueError):break
tag=('XDG_RUNTIME_DIR='+str(runtime)).encode()
def targets():
 for d in Path('/proc').iterdir():
  if not d.name.isdigit() or int(d.name) in ancestors:continue
  try:
   if d.stat().st_uid==os.getuid() and tag in (d/'environ').read_bytes().split(b'\0'):yield int(d.name)
  except (OSError,ProcessLookupError):pass
for sig in [signal.SIGTERM,signal.SIGKILL]:
 for pid in targets():
  try:os.kill(pid,sig)
  except ProcessLookupError:pass
 if sig==signal.SIGTERM:time.sleep(.3)
