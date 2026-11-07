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

def parse_snap_inventory(list_out: str, refresh_out: str) -> list[InstalledItem]:
    updates: dict[str, str] = {}
    refresh_lines = refresh_out.strip().splitlines()
    if len(refresh_lines) > 1:
        for line in refresh_lines[1:]:
            parts = line.split()
            if len(parts) >= 2:
                updates[parts[0]] = parts[1]

    items = []
    list_lines = list_out.strip().splitlines()
    if len(list_lines) > 1:
        for line in list_lines[1:]:
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0]
                installed_ver = parts[1]
                if name in updates:
                    items.append(
                        InstalledItem(
                            id=f"snap:{name}",
                            name=name,
                            category=Category.APPS,
                            ecosystem="snap",
                            installed_version=installed_ver,
                            latest_version=updates[name],
                            status=Status.OUTDATED,
                            update_command=f"sudo snap refresh {name}",
                            description=f"Snap application ({name})",
                        )
                    )
                else:
                    items.append(
                        InstalledItem(
                            id=f"snap:{name}",
                            name=name,
                            category=Category.APPS,
                            ecosystem="snap",
                            installed_version=installed_ver,
                            latest_version=installed_ver,
                            status=Status.UP_TO_DATE,
                            update_command="",
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

def parse_flatpak_inventory(list_out: str, updates_out: str) -> list[InstalledItem]:
    updates: dict[str, str] = {}
    for line in updates_out.strip().splitlines():
        parts = line.split()
        if len(parts) >= 2:
            updates[parts[0]] = parts[1]

    items = []
    for line in list_out.strip().splitlines():
        if not line.strip() or line.startswith("Application ID"):
            continue
        parts = [p.strip() for p in line.split("\t") if p.strip()]
        if not parts:
            parts = line.split()
        if len(parts) >= 1:
            app_id = parts[0]
            ver = parts[1] if len(parts) >= 2 else ""
            app_name = parts[2] if len(parts) >= 3 else app_id
            if app_id in updates:
                items.append(
                    InstalledItem(
                        id=f"flatpak:{app_id}",
                        name=app_name,
                        category=Category.APPS,
                        ecosystem="flatpak",
                        installed_version=ver,
                        latest_version=updates[app_id],
                        status=Status.OUTDATED,
                        update_command=f"flatpak update -y {app_id}",
                        description=f"Flatpak package ({app_id})",
                    )
                )
            else:
                items.append(
                    InstalledItem(
                        id=f"flatpak:{app_id}",
                        name=app_name,
                        category=Category.APPS,
                        ecosystem="flatpak",
                        installed_version=ver,
                        latest_version=ver,
                        status=Status.UP_TO_DATE,
                        update_command="",
                        description=f"Flatpak package ({app_id})",
                    )
                )
    return items

def parse_apt_inventory(upgradable_out: str, manual_names: set[str], installed_pkgs: dict[str, str]) -> list[InstalledItem]:
    upgradable_items = parse_apt_upgradable(upgradable_out)
    upgradable_pkg_names = {i.name for i in upgradable_items}

    items = list(upgradable_items)
    for pkg in sorted(manual_names):
        if pkg in upgradable_pkg_names:
            continue
        ver = installed_pkgs.get(pkg, "")
        if ver:
            items.append(
                InstalledItem(
                    id=f"apt:{pkg}",
                    name=pkg,
                    category=Category.SYSTEM,
                    ecosystem="apt",
                    installed_version=ver,
                    latest_version=ver,
                    status=Status.UP_TO_DATE,
                    update_command="",
                    description=f"Debian/Ubuntu package ({pkg})",
                )
            )
    return items

def build_batch_update_commands(items: list[InstalledItem], elevate: str = "sudo") -> list[tuple[str, list[str]]]:
    """Group items by ecosystem into single atomic update commands where supported."""
    batches: list[tuple[str, list[str]]] = []

    apt_items = [i for i in items if i.ecosystem == "apt" and i.status == Status.OUTDATED]
    snap_items = [i for i in items if i.ecosystem == "snap" and i.status == Status.OUTDATED]
    flatpak_items = [i for i in items if i.ecosystem == "flatpak" and i.status == Status.OUTDATED]
    npm_items = [i for i in items if i.ecosystem == "npm" and i.status == Status.OUTDATED]
    pip_items = [i for i in items if i.ecosystem == "pip" and i.status == Status.OUTDATED]
    other_items = [i for i in items if i.ecosystem not in ("apt", "snap", "flatpak", "npm", "pip") and i.status == Status.OUTDATED]

    if apt_items:
        names = " ".join(i.name for i in apt_items)
        batches.append((f"{elevate} apt-get install --only-upgrade -y {names}", [i.id for i in apt_items]))

    if snap_items:
        names = " ".join(i.name for i in snap_items)
        batches.append((f"{elevate} snap refresh {names}", [i.id for i in snap_items]))

    if flatpak_items:
        ids = " ".join(i.id.replace("flatpak:", "") for i in flatpak_items)
        batches.append((f"flatpak update -y {ids}", [i.id for i in flatpak_items]))

    if npm_items:
        names = " ".join(f"{i.name}@latest" for i in npm_items)
        batches.append((f"npm install -g {names}", [i.id for i in npm_items]))

    if pip_items:
        user_flag = " --user" if any("--user" in (i.update_command or "") for i in pip_items) else ""
        names = " ".join(i.name for i in pip_items)
        batches.append((f"pip install{user_flag} -U {names}", [i.id for i in pip_items]))

    for item in other_items:
        if item.update_command:
            batches.append((item.update_command, [item.id]))

    return batches

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

def parse_custom_tools(json_str: str) -> list[InstalledItem]:
    items = []
    try:
        data = json.loads(json_str)
        tools_list = data if isinstance(data, list) else data.get("tools", [])
        for entry in tools_list:
            items.append(
                InstalledItem(
                    id=entry.get("id", f"custom:{entry.get('name', 'tool')}"),
                    name=entry.get("name", "Custom Tool"),
                    category=Category.TOOLS,
                    ecosystem="custom",
                    installed_version=entry.get("installed_version", ""),
                    latest_version=entry.get("latest_version"),
                    update_command=entry.get("update_command", ""),
                    description=entry.get("description", "Custom configured tool"),
                )
            )
    except Exception:
        pass
    return items

def scan_custom_tools(tools_path: Optional[Path] = None) -> list[InstalledItem]:
    path = tools_path or (Path.home() / ".config" / "updatymeow" / "tools.json")
    if not path.exists():
        return []
    try:
        return parse_custom_tools(path.read_text(encoding="utf-8"))
    except Exception:
        return []

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
    upgradable_out = _run_cmd(["apt", "list", "--upgradable"])
    manual_names: set[str] = set()
    if shutil.which("apt-mark"):
        manual_out = _run_cmd(["apt-mark", "showmanual"])
        manual_names = {l.strip() for l in manual_out.splitlines() if l.strip()}

    installed_pkgs: dict[str, str] = {}
    if shutil.which("dpkg-query"):
        dpkg_out = _run_cmd(["dpkg-query", "-W", "-f=${binary:Package}\t${Version}\t${db:Status-Status}\n"])
        for line in dpkg_out.splitlines():
            parts = line.split("\t")
            if len(parts) >= 3 and parts[2] == "installed":
                installed_pkgs[parts[0]] = parts[1]

    return parse_apt_inventory(upgradable_out, manual_names, installed_pkgs)

def scan_snap() -> list[InstalledItem]:
    if not shutil.which("snap"):
        return []
    list_out = _run_cmd(["snap", "list"])
    refresh_out = _run_cmd(["snap", "refresh", "--list"])
    return parse_snap_inventory(list_out, refresh_out)

def scan_flatpak() -> list[InstalledItem]:
    if not shutil.which("flatpak"):
        return []
    list_out = _run_cmd(["flatpak", "list", "--columns=application,version,name"])
    updates_out = _run_cmd(["flatpak", "remote-ls", "--updates", "--columns=application,version"])
    return parse_flatpak_inventory(list_out, updates_out)

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
    scanners = [scan_apt, scan_snap, scan_flatpak, scan_npm, scan_pip, scan_runtimes, scan_custom_tools]
    results = []
    with ThreadPoolExecutor(max_workers=len(scanners)) as ex:
        futures = [ex.submit(s) for s in scanners]
        for f in futures:
            try:
                results.extend(f.result())
            except Exception:
                pass
    return results

