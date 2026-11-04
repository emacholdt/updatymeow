import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional
from updatymeow.models import Category, InstalledItem, Status

_APT_LINE_RE = re.compile(r"^([^/\s]+)/[^\s]+\s+([^\s]+)\s+[^\s]+\s+\[upgradable from:\s+([^\]]+)\]")

def parse_apt_upgradable(output: str) -> list[InstalledItem]:
    items = []
    elevate = "pkexec" if shutil.which("pkexec") else "sudo"
    for line in output.splitlines():
        line = line.strip()
        m = _APT_LINE_RE.match(line)
        if m:
            pkg, new_ver, old_ver = m.groups()
            items.append(
                InstalledItem(
                    id=f"apt:{pkg}",
                    name=pkg,
                    category=Category.SYSTEM,
                    ecosystem="apt",
                    installed_version=old_ver,
                    latest_version=new_ver,
                    update_command=f"{elevate} apt-get install --only-upgrade -y {pkg}",
                    description=f"Debian/Ubuntu package ({pkg})",
                )
            )
    return items

def parse_snap_refresh_list(output: str) -> list[InstalledItem]:
    items = []
    lines = output.strip().splitlines()
    if len(lines) <= 1:
        return items
    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 2:
            name, new_ver = parts[0], parts[1]
            items.append(
                InstalledItem(
                    id=f"snap:{name}",
                    name=name,
                    category=Category.APPS,
                    ecosystem="snap",
                    installed_version="",
                    latest_version=new_ver,
                    status=Status.OUTDATED,
                    update_command=f"sudo snap refresh {name}",
                    description=f"Snap application ({name})",
                )
            )
    return items

def parse_flatpak_updates(output: str) -> list[InstalledItem]:
    items = []
    for line in output.strip().splitlines():
        parts = [p.strip() for p in line.split("\t") if p.strip()]
        if len(parts) >= 3:
            app_id, curr_ver, new_ver = parts[0], parts[1], parts[2]
            items.append(
                InstalledItem(
                    id=f"flatpak:{app_id}",
                    name=app_id,
                    category=Category.APPS,
                    ecosystem="flatpak",
                    installed_version=curr_ver,
                    latest_version=new_ver,
                    update_command=f"flatpak update -y {app_id}",
                    description=f"Flatpak package ({app_id})",
                )
            )
    return items

def parse_npm_outdated(json_str: str) -> list[InstalledItem]:
    items = []
    try:
        data = json.loads(json_str)
        if isinstance(data, dict):
            for pkg, info in data.items():
                curr = info.get("current", "")
                latest = info.get("latest", "")
                items.append(
                    InstalledItem(
                        id=f"npm:{pkg}",
                        name=pkg,
                        category=Category.PACKAGES,
                        ecosystem="npm",
                        installed_version=curr,
                        latest_version=latest,
                        update_command=f"npm install -g {pkg}@latest",
                        description=f"NPM global package ({pkg})",
                    )
                )
    except Exception:
        pass
    return items

def parse_pip_outdated(json_str: str, is_user: bool = False) -> list[InstalledItem]:
    items = []
    user_flag = " --user" if is_user else ""
    try:
        data = json.loads(json_str)
        if isinstance(data, list):
            for entry in data:
                name = entry.get("name", "")
                ver = entry.get("version", "")
                latest = entry.get("latest_version", "")
                items.append(
                    InstalledItem(
                        id=f"pip:{name}",
                        name=name,
                        category=Category.PACKAGES,
                        ecosystem="pip",
                        installed_version=ver,
                        latest_version=latest,
                        update_command=f"pip install{user_flag} -U {name}",
                        description=f"Python package ({name})",
                    )
                )
    except Exception:
        pass
    return items

def _run_cmd(cmd: list[str], timeout: int = 25) -> str:
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return res.stdout
    except Exception:
        return ""

def scan_apt() -> list[InstalledItem]:
    if not shutil.which("apt"):
        return []
    out = _run_cmd(["apt", "list", "--upgradable"])
    return parse_apt_upgradable(out)

def scan_snap() -> list[InstalledItem]:
    if not shutil.which("snap"):
        return []
    out = _run_cmd(["snap", "refresh", "--list"])
    return parse_snap_refresh_list(out)

def scan_flatpak() -> list[InstalledItem]:
    if not shutil.which("flatpak"):
        return []
    # shortcut: query remote updates using standard flatpak command
    out = _run_cmd(["flatpak", "remote-ls", "--updates", "--columns=application,version"])
    items = []
    for line in out.strip().splitlines():
        parts = line.split()
        if len(parts) >= 2:
            app_id, new_ver = parts[0], parts[1]
            items.append(
                InstalledItem(
                    id=f"flatpak:{app_id}",
                    name=app_id,
                    category=Category.APPS,
                    ecosystem="flatpak",
                    installed_version="",
                    latest_version=new_ver,
                    status=Status.OUTDATED,
                    update_command=f"flatpak update -y {app_id}",
                    description=f"Flatpak application ({app_id})",
                )
            )
    return items

def scan_npm() -> list[InstalledItem]:
    if not shutil.which("npm"):
        return []
    out = _run_cmd(["npm", "-g", "outdated", "--json"])
    return parse_npm_outdated(out)

def scan_pip() -> list[InstalledItem]:
    pip_cmd = "pip" if shutil.which("pip") else None
    if not pip_cmd:
        return []
    # shortcut: on PEP 668 systems only scan --user to prevent conflicting with APT packages
    marker = Path(sys.prefix) / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "EXTERNALLY-MANAGED"
    if marker.exists():
        out = _run_cmd([pip_cmd, "list", "--user", "--outdated", "--format=json"])
        return parse_pip_outdated(out, is_user=True)
    out = _run_cmd([pip_cmd, "list", "--outdated", "--format=json"])
    return parse_pip_outdated(out, is_user=False)

def scan_runtimes() -> list[InstalledItem]:
    items = []
    runtimes = [
        ("node", ["node", "-v"], Category.RUNTIMES, r"v(\S+)"),
        ("python3", ["python3", "--version"], Category.RUNTIMES, r"Python (\S+)"),
        ("uv", ["uv", "--version"], Category.RUNTIMES, r"uv (\S+)"),
        ("rustc", ["rustc", "--version"], Category.RUNTIMES, r"rustc (\S+)"),
    ]
    for name, cmd, cat, pat in runtimes:
        if shutil.which(cmd[0]):
            out = _run_cmd(cmd)
            m = re.search(pat, out)
            ver = m.group(1) if m else "installed"
            items.append(
                InstalledItem(
                    id=f"runtime:{name}",
                    name=name,
                    category=cat,
                    ecosystem="runtime",
                    installed_version=ver,
                    latest_version=ver,
                    status=Status.UP_TO_DATE,
                    update_command="",
                    description=f"{name} development runtime",
                )
            )
    return items

def scan_all_ecosystems() -> list[InstalledItem]:
    scanners = [scan_apt, scan_snap, scan_flatpak, scan_npm, scan_pip, scan_runtimes]
    results = []
    with ThreadPoolExecutor(max_workers=len(scanners)) as ex:
        futures = [ex.submit(s) for s in scanners]
        for f in futures:
            try:
                results.extend(f.result())
            except Exception:
                pass
    return results

