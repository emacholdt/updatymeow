from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, Any
from updatymeow.version import compare_versions, is_major_update

class Category(str, Enum):
    SYSTEM = "System"
    APPS = "Apps"
    RUNTIMES = "Runtimes"
    PACKAGES = "Packages"
    TOOLS = "Tools"

class Status(str, Enum):
    UP_TO_DATE = "Up to date"
    OUTDATED = "Update available"
    PINNED = "Pinned"
    UNKNOWN = "Unknown"

@dataclass
class InstalledItem:
    id: str
    name: str
    category: Category
    ecosystem: str
    installed_version: str
    latest_version: Optional[str] = None
    update_command: str = ""
    description: str = ""
    is_pinned: bool = False
    is_favorite: bool = False
    status: Status = Status.UNKNOWN
    is_major: bool = False

    def __post_init__(self):
        if self.is_pinned:
            self.status = Status.PINNED
            return

        if not self.latest_version:
            self.status = Status.UNKNOWN
            self.is_major = False
            return

        cmp = compare_versions(self.installed_version, self.latest_version)
        if cmp < 0:
            self.status = Status.OUTDATED
            self.is_major = is_major_update(self.installed_version, self.latest_version)
        else:
            self.status = Status.UP_TO_DATE
            self.is_major = False

@dataclass
class UpdateRecord:
    timestamp: str
    item_id: str
    item_name: str
    from_version: str
    to_version: str
    success: bool
    output: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UpdateRecord":
        return cls(**data)
