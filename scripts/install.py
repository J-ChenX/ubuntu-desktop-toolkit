#!/usr/bin/python3
"""Install explicitly selected desktop modules, backing up user configuration first."""
import argparse, datetime, hashlib, json, os, shlex, shutil, subprocess, tempfile, stat
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
HOME_DIR = Path.home()
COMPONENTS = json.loads((ROOT/'components.json').read_text())
FILE_RELEASE = ROOT/COMPONENTS['file_manager']['release_dir']
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('module', choices=['terminal', 'file-manager', 'sogou', 'all'])
parser.add_argument('--check', action='store_true', help='read-only preflight; do not install')
parser.add_argument('--selection-style', action='store_true', help='append the saved Nautilus selection style')
parser.add_argument('--project-menu', action='store_true', help='include the optional project launch menu')
args = parser.parse_args()

def run(*cmd):
    subprocess.run(list(map(str, cmd)), check=True)

def verify():
    for line in (ROOT/'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != digest:
            raise SystemExit('文件校验失败：'+name)

verify()
# Downloaded assets are optional repository content, mandatory for their module.
external = json.loads((ROOT/'external-assets.json').read_text())['files']
required = {name: digest for name, digest in external.items()
            if args.module == 'all' or
            (args.module == 'terminal' and name.startswith('modules/terminal/')) or
            (args.module == 'sogou' and name.startswith('modules/input-method/'))}
problems = []
for name, digest in required.items():
    path = ROOT/name
    if not path.is_file(): problems.append('缺少：'+name)
    elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        problems.append('版本或 SHA256 不匹配：'+name)
if problems:
    raise SystemExit('\n'.join(problems)+'\n请按 docs/下载依赖.md 准备依赖，再重新执行 --check；未修改系统。')
release = dict(line.split('=', 1) for line in Path('/etc/os-release').read_text().splitlines() if '=' in line)
if release.get('ID', '').strip('"') != 'ubuntu' or release.get('VERSION_ID', '').strip('"') != '22.04':
    raise SystemExit('本工具包只验证了 Ubuntu 22.04；其他版本需重新适配，停止安装。')
if subprocess.check_output(['dpkg', '--print-architecture'], text=True).strip() != 'amd64':
    raise SystemExit('当前预编译包要求 amd64。')
if os.getuid() == 0:
    raise SystemExit('请以目标桌面用户执行，不要 sudo 整个脚本；系统安装步骤会单独调用 sudo。')
print('校验通过；目标用户：', HOME_DIR, '模块：', args.module, flush=True)
if args.check:
    print('只读检查完成，未安装或修改配置。')
    raise SystemExit(0)
from gi.repository import Gio
if args.module in ('terminal', 'file-manager', 'all'):
    Gio.bus_get_sync(Gio.BusType.SESSION, None)
backup = HOME_DIR/'.local/state/ubuntu-desktop-toolkit/backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
backup.mkdir(parents=True)
state = {'files': {}, 'settings': {}, 'module': args.module}

def atomic_write(path, data, mode=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    current_mode = stat.S_IMODE(path.stat().st_mode) if path.is_file() and not path.is_symlink() else 0o644
    fd, name = tempfile.mkstemp(prefix='.'+path.name+'.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fchmod(stream.fileno(), mode if mode is not None else current_mode)
            os.fsync(stream.fileno())
        os.replace(name, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(directory_fd)
        finally: os.close(directory_fd)
    finally:
        if os.path.exists(name): os.unlink(name)

def save_state():
    atomic_write(backup/'manifest.json', json.dumps(state, ensure_ascii=False, indent=2).encode(), 0o600)

def remember(path):
    path = Path(path)
    key = str(path.relative_to(HOME_DIR))
    if key in state['files']:
        return
    exists = path.exists() or path.is_symlink()
    state['files'][key] = exists
    if exists:
        dest = backup/'files'/key
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest, follow_symlinks=False)
    save_state()

def write(path, text, executable=False):
    path = Path(path)
    data = text.encode()
    if path.is_file() and not path.is_symlink() and path.read_bytes() == data:
        if executable and stat.S_IMODE(path.stat().st_mode) != 0o755:
            remember(path)
            path.chmod(0o755)
        return
    remember(path)
    atomic_write(path, data, 0o755 if executable else None)

def copy(src, dst):
    dst = Path(dst)
    if dst.is_file() and not dst.is_symlink() and hashlib.sha256(dst.read_bytes()).digest() == hashlib.sha256(Path(src).read_bytes()).digest(): return
    remember(dst)
    atomic_write(dst, Path(src).read_bytes(), stat.S_IMODE(Path(src).stat().st_mode))

def setting(schema, key, value):
    obj = Gio.Settings.new(schema)
    if obj.get_value(key).unpack() == value: return
    state['settings'][schema+' '+key] = obj.get_value(key).print_(True)
    save_state()
    if isinstance(value, bool): obj.set_boolean(key, value)
    elif isinstance(value, list): obj.set_strv(key, value)
    else: obj.set_string(key, value)
    Gio.Settings.sync()

run('sudo', 'apt-get', 'update')
if args.module in ('terminal', 'all'):
    run('sudo', 'apt-get', 'install', 'terminator', 'fonts-dejavu-core', 'fontconfig', 'yaru-theme-gtk')
    module = ROOT/'modules/terminal'
    copy(module/'launch.py', HOME_DIR/'.local/lib/terminator-themed/launch.py')
    write(HOME_DIR/'.local/bin/terminator-themed', (module/'terminator-themed').read_text(), True)
    config = (ROOT/COMPONENTS['terminal']['profile']).read_text()
    if args.project_menu:
        config = config[:config.index('[plugins]')] + (module/'config/project-menu.example.conf').read_text()
        config = config.replace('cd ${HOME}/code/example-project', 'cd '+shlex.quote(str(HOME_DIR/'code/example-project')))
    write(HOME_DIR/'.config/terminator/config', config)
    for font in [*(ROOT/name for name in required if name.startswith('modules/terminal/')), module/'fonts/LICENSE.txt']:
        copy(font, HOME_DIR/'.local/share/fonts/MapleMono-NF-CN'/font.name)
    run('fc-cache', '-f', HOME_DIR/'.local/share/fonts/MapleMono-NF-CN')
    launcher = str(HOME_DIR/'.local/bin/terminator-themed')
    quoted = '"'+launcher.replace('\\', '\\\\').replace('"', '\\"')+'"'
    write(HOME_DIR/'.local/share/applications/terminator.desktop', '[Desktop Entry]\nName=Terminator\nType=Application\nExec='+quoted+'\nIcon=utilities-terminal\nCategories=System;TerminalEmulator;\nStartupNotify=true\nActions=NewWindow;\n\n[Desktop Action NewWindow]\nName=Open a New Window\nExec='+quoted+'\n')
    setting('org.gnome.desktop.default-applications.terminal', 'exec', launcher)
    setting('org.gnome.desktop.default-applications.terminal', 'exec-arg', '-x')
    setting('org.gnome.settings-daemon.plugins.media-keys', 'terminal', ['<Primary><Alt>t'])
if args.module in ('file-manager', 'all'):
    module = ROOT/'modules/file-manager'
    run('sudo', 'apt-get', 'install', *sorted((FILE_RELEASE/'packages').glob('*.deb')))
    setting('org.gnome.nautilus.preferences', 'use-experimental-views', True)
    schema = 'org.gnome.settings-daemon.plugins.xsettings'
    modules = Gio.Settings.new(schema).get_strv('enabled-gtk-modules')
    setting(schema, 'enabled-gtk-modules', list(dict.fromkeys(modules+['gtk-filechooser-click-path'])))
    write(HOME_DIR/'.config/systemd/user/xdg-desktop-portal-gnome.service.d/90-click-path.conf', '[Service]\nEnvironment="LD_PRELOAD=/usr/lib/local-portal-click-path/libportal-click-path.so"\n')
    run('systemctl', '--user', 'daemon-reload')
    run('sudo', 'touch', '/usr/lib/gnome-settings-daemon-3.0/gtk-modules/local-gtk-filechooser-click-path.refresh')
    # Repair older user-level overrides which otherwise shadow the installed executable.
    launcher = HOME_DIR/'.local/bin/nautilus'
    if launcher.exists() or launcher.is_symlink():
        remember(launcher); launcher.unlink(); launcher.symlink_to('/usr/bin/nautilus')
    for rel in ['.local/share/applications/org.gnome.Nautilus.desktop', '.local/share/dbus-1/services/org.gnome.Nautilus.service', '.local/share/dbus-1/services/org.freedesktop.FileManager1.service']:
        path = HOME_DIR/rel
        if path.exists():
            lines = path.read_text().splitlines()
            lines = [('Exec=/usr/bin/nautilus --gapplication-service' if rel.endswith('.service') else 'Exec=/usr/bin/nautilus --new-window %U') if line.startswith('Exec=') else ('TryExec=/usr/bin/nautilus' if line.startswith('TryExec=') else line) for line in lines]
            write(path, '\n'.join(lines)+'\n')
    extension = HOME_DIR/'.local/share/nautilus-python/extensions/themed_terminal.py'
    if extension.exists(): remember(extension); extension.unlink()
    if args.selection_style:
        css = HOME_DIR/'.config/gtk-3.0/gtk.css'
        original = css.read_text() if css.exists() else ''
        begin = '/* BEGIN synced Nautilus selection */'; end = '/* END synced Nautilus selection */'
        if begin in original and end in original:
            original = original[:original.index(begin)] + original[original.index(end)+len(end):]
        write(css, original.rstrip()+'\n\n'+(module/'selection.css').read_text())
if args.module in ('sogou', 'all'):
    run('sudo', 'apt-get', 'install', 'fcitx', 'fcitx-config-gtk', 'im-config', 'language-pack-zh-hans', 'libqt5qml5', 'libqt5quick5', 'libqt5quickwidgets5', 'qml-module-qtquick2', 'libgsettings-qt1', ROOT/COMPONENTS['sogou']['package_file'])
    remember(HOME_DIR/'.xinputrc')
    run('im-config', '-n', 'fcitx')
    profile = HOME_DIR/'.profile'; text = profile.read_text() if profile.exists() else ''
    exports = ['export GTK_IM_MODULE=fcitx', 'export QT_IM_MODULE=fcitx', 'export XMODIFIERS=@im=fcitx']
    additions = [line for line in exports if line not in text.splitlines()]
    if additions: write(profile, text+'\n# Ubuntu desktop toolkit: Fcitx 4\n'+'\n'.join(additions)+'\n')
    write(HOME_DIR/'.config/autostart/fcitx.desktop', '[Desktop Entry]\nType=Application\nName=Fcitx\nExec=fcitx\nTerminal=false\nX-GNOME-Autostart-enabled=true\n')
save_state()
print('安装完成。配置备份：', backup)
print('保存工作后注销并重新登录，使文件管理器、portal、输入法和终端入口统一生效。脚本没有强制关闭窗口。')
