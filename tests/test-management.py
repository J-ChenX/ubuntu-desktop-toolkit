#!/usr/bin/python3
import ast,hashlib,json,os,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as td:
 root=Path(td);(root/'bin').mkdir();shutil.copy2(ROOT/'bin/desktopctl',root/'bin/desktopctl')
 (root/'value').write_text('valid');digest=hashlib.sha256(b'valid').hexdigest()
 (root/'SHA256SUMS').write_text(digest+'  value\n')
 def run(*args):return subprocess.run([str(root/'bin/desktopctl'),*args],capture_output=True)
 assert run('check').returncode==0
 (root/'value').write_text('tampered');assert run('check').returncode!=0
 (root/'value').write_text('valid');(root/'escape').symlink_to('/etc/hostname')
 (root/'SHA256SUMS').write_text(hashlib.sha256(Path('/etc/hostname').read_bytes()).hexdigest()+'  escape\n');assert run('check').returncode!=0
 assert run('sync','-bad:dest').returncode!=0
 assert run('unknown').returncode!=0
 print('PASS native manager rejects tampered manifests, escaping paths and invalid commands')
 # Exercise actual atomic writer in a temporary directory, without running installer.
 module=ast.parse((ROOT/'scripts/install.py').read_text());node=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='atomic_write')
 scope={'Path':Path,'os':os,'tempfile':tempfile,'stat':__import__('stat')};exec(compile(ast.Module(body=[node],type_ignores=[]),'atomic-write-test','exec'),scope)
 target=root/'config';target.write_text('old');scope['atomic_write'](target,b'new',0o600);assert target.read_bytes()==b'new';assert target.stat().st_mode&0o777==0o600
 external=root/'external';external.write_text('untouched');target.unlink();target.symlink_to(external)
 scope['atomic_write'](target,b'replacement');assert external.read_text()=='untouched' and not target.is_symlink()
 assert not list(root.glob('.config.*'))
 print('PASS atomic configuration replacement preserves unrelated symlink target and cleans temporary files')
