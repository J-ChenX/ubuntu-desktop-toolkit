#!/usr/bin/python3
"""Read-only checks for the public repository and release metadata."""
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = dict(line.split('  ', 1)[::-1] for line in (ROOT/'SHA256SUMS').read_text().splitlines())
tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
tracked = {name for name in tracked if name}
assert tracked == set(manifest) | {'SHA256SUMS'}, 'Git tracking and SHA256SUMS differ'
external = json.loads((ROOT/'external-assets.json').read_text())['files']
assert not set(external) & tracked, 'Downloaded assets must not be committed'
for name in external:
    assert subprocess.run(['git','check-ignore','-q',name], cwd=ROOT).returncode == 0, name
for name, digest in manifest.items():
    p = ROOT/name
    assert hashlib.sha256(p.read_bytes()).hexdigest() == digest, name
    if name.endswith('.py') and 'vendor/' not in name:
        ast.parse(p.read_text(), filename=name)
for name in tracked:
    if name.endswith('.md') and not name.startswith('src/desktopctl/vendor/'):
        p = ROOT/name
        for link in re.findall(r'\]\(([^)]+)\)', p.read_text()):
            if '://' not in link and not link.startswith(('mailto:', '#')):
                assert (p.parent/link.split('#')[0]).exists(), (name, link)
components = json.loads((ROOT/'components.json').read_text())
release = ROOT/components['file_manager']['release_dir']
info = json.loads((release/'manifest.json').read_text())
assert components['file_manager']['version'] == info['version']
assert {p.name for p in (release/'packages').glob('*.deb')} == set(info['packages'])
for name, digest in info['packages'].items():
    assert hashlib.sha256((release/'packages'/name).read_bytes()).hexdigest() == digest
print('PASS tracked files, excluded downloads, checksums, Python syntax, documentation links and package manifest')
