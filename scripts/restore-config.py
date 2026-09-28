#!/usr/bin/python3
"""Restore user configuration saved by install.py (does not downgrade packages)."""
import argparse,json,os,shutil,subprocess
from pathlib import Path
from gi.repository import Gio,GLib
p=argparse.ArgumentParser(description=__doc__);p.add_argument('backup',type=Path);p.add_argument('--apply',action='store_true');a=p.parse_args()
base=a.backup.resolve();state=json.loads((base/'manifest.json').read_text());home_dir=Path.home()
if os.getuid()==0:raise SystemExit('请以目标桌面用户运行。')
for rel,existed in state['files'].items():
 if Path(rel).is_absolute() or '..' in Path(rel).parts:raise SystemExit('无效备份路径')
 print('恢复' if existed else '移除安装新增文件',rel)
for k in state['settings']:print('恢复设置',k)
if not a.apply:raise SystemExit('仅预览；添加 --apply 才会恢复。')
for rel,existed in state['files'].items():
 target=home_dir/rel
 if target.is_symlink() or target.is_file():target.unlink()
 if existed:
  target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(base/'files'/rel,target,follow_symlinks=False)
for compound,value in state['settings'].items():
 schema,key=compound.split(' ',1);s=Gio.Settings.new(schema);s.set_value(key,GLib.Variant.parse(s.get_value(key).get_type(),value,None,None))
Gio.Settings.sync()
subprocess.run(['systemctl','--user','daemon-reload'],check=True)
subprocess.run(['fc-cache','-f'],check=True)
print('配置已恢复；软件包版本不变。请保存工作后注销并重新登录。')
