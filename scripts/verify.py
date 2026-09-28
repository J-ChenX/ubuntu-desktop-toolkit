#!/usr/bin/python3
"""Verify toolkit files and report installed versions without changing settings."""
import hashlib,json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
if '--status' not in sys.argv:
 for line in (root/'SHA256SUMS').read_text().splitlines():
  expected,name=line.split('  ',1)
  assert hashlib.sha256((root/name).read_bytes()).hexdigest()==expected,name
 print('工具包全部文件校验通过')
subprocess.run(['dpkg-query','-W','nautilus','nautilus-data','libnautilus-extension1a','local-gtk-filechooser-click-path','local-portal-click-path','terminator','sogoupinyin','fcitx'])
expected=json.loads((root/json.loads((root/'components.json').read_text())['file_manager']['release_dir']/'manifest.json').read_text())['nautilus_sha256']
binary=Path('/usr/bin/nautilus')
print('当前安装的 Nautilus 与当前发布匹配：',binary.exists() and hashlib.sha256(binary.read_bytes()).hexdigest()==expected)
try:
 from gi.repository import Gio,GLib
 b=Gio.bus_get_sync(Gio.BusType.SESSION,None)
 pid=b.call_sync('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','GetConnectionUnixProcessID',GLib.Variant('(s)',('org.gnome.Nautilus',)),None,0,3000,None).unpack()[0]
 print('运行中的 Nautilus 与当前发布匹配：',hashlib.sha256(Path('/proc',str(pid),'exe').read_bytes()).hexdigest()==expected)
except Exception as e:print('未获取到桌面 Nautilus 运行状态：',e)
