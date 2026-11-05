"""Validated, user-scoped Sonny dashboard personalization settings.

Pure model: no network calls, database writes, or permission changes.
A future authenticated API must derive the account ID from its bearer session.
"""
from dataclasses import dataclass
from typing import Tuple

ALLOWED_BLOCKS = frozenset({
    "voice", "projects", "github", "business", "vision", "creative",
    "meemaw_papa", "social", "memory", "calendar", "system", "activity"
})
ALLOWED_THEMES = frozenset({"midnight", "light", "high_contrast"})
ALLOWED_AVATARS = frozenset({"classic", "professional", "friendly", "minimal", "none"})
MAX_COLUMNS = 12


@dataclass(frozen=True)
class DashboardBlock:
    key: str
    x: int
    y: int
    width: int = 3
    height: int = 2

    def __post_init__(self):
        if self.key not in ALLOWED_BLOCKS:
            raise ValueError("unknown dashboard block")
        if any(type(n) is not int for n in (self.x, self.y, self.width, self.height)):
            raise ValueError("coordinates and dimensions must be integers")
        if self.x < 0 or self.y < 0 or self.width < 1 or self.height < 1:
            raise ValueError("invalid block bounds")
        if self.x + self.width > MAX_COLUMNS or self.y + self.height > 100:
            raise ValueError("block outside dashboard grid")


@dataclass(frozen=True)
class Personalization:
    account_id: str
    avatar: str = "classic"
    theme: str = "midnight"
    blocks: Tuple[DashboardBlock, ...] = ()

    def __post_init__(self):
        if not self.account_id or not self.account_id.strip():
            raise ValueError("authenticated account required")
        if self.avatar not in ALLOWED_AVATARS or self.theme not in ALLOWED_THEMES:
            raise ValueError("unsupported avatar or theme")
        if len(self.blocks) > len(ALLOWED_BLOCKS):
            raise ValueError("too many blocks")
        if len({block.key for block in self.blocks}) != len(self.blocks):
            raise ValueError("duplicate block")
        for index, a in enumerate(self.blocks):
            for b in self.blocks[index + 1:]:
                if (a.x < b.x + b.width and b.x < a.x + a.width
                        and a.y < b.y + b.height and b.y < a.y + a.height):
                    raise ValueError("overlapping blocks")

    def update(self, account_id: str, *, avatar=None, theme=None, blocks=None):
        if account_id != self.account_id:
            raise PermissionError("account mismatch")
        return Personalization(
            account_id=self.account_id,
            avatar=self.avatar if avatar is None else avatar,
            theme=self.theme if theme is None else theme,
            blocks=self.blocks if blocks is None else tuple(blocks),
        )
