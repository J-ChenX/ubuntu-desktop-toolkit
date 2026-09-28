#!/usr/bin/python3
import hashlib, json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
external=set(json.loads((root/'external-assets.json').read_text())['files'])
files=[p for p in root.rglob('*') if p.is_file() and str(p.relative_to(root)) not in external and 'downloads' not in p.relative_to(root).parts and not (p.parent == root/'modules/terminal/fonts' and p.suffix in {'.ttf','.otf'}) and not (p.parent == root/'modules/input-method/packages' and p.suffix == '.deb') and p!=root/'SHA256SUMS' and not any(part in {'__pycache__','.git','work','backups'} for part in p.relative_to(root).parts)]
(root/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(root))+'\n' for p in sorted(files)))
print('已更新',len(files),'个文件的校验值')
