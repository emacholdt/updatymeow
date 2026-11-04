import re

_NUM_RE = re.compile(r"\d+")

def parse_version_tuple(ver_str: str) -> tuple[int, ...]:
    # shortcut: extracts digits only; when complex pre-releases matter, use packaging.version
    nums = [int(m) for m in _NUM_RE.findall(ver_str or "")]
    return tuple(nums) if nums else (0,)

def compare_versions(v1: str, v2: str) -> int:
    t1 = parse_version_tuple(v1)
    t2 = parse_version_tuple(v2)
    # Pad to equal length
    max_len = max(len(t1), len(t2))
    p1 = t1 + (0,) * (max_len - len(t1))
    p2 = t2 + (0,) * (max_len - len(t2))
    return (p1 > p2) - (p1 < p2)

def is_major_update(current: str, latest: str) -> bool:
    t1 = parse_version_tuple(current)
    t2 = parse_version_tuple(latest)
    return len(t1) > 0 and len(t2) > 0 and t2[0] > t1[0]

