"""The ``ProteaseInfo`` dataclass: a protease's cleavage regex and identifying names."""

import re
from dataclasses import dataclass

__all__ = ["ProteaseInfo"]


@dataclass(frozen=True, slots=True)
class ProteaseInfo:
    """A digestion enzyme and its cleavage-site regex."""

    id: str
    """Id, e.g. ``"trypsin"``."""
    name: str
    """Short name, e.g. ``"Trypsin"``."""
    full_name: str
    """Descriptive name, e.g. ``"Trypsin with proline restriction"``."""
    regex: str
    """Zero-width regex matching the cleavage sites, e.g. ``"(?<=[KR])(?=[^P])"``."""

    @property
    def pattern(self) -> re.Pattern[str]:
        """:attr:`regex`, compiled (served from ``re``'s compile cache after the first call)."""
        return re.compile(self.regex)

    def to_dict(self) -> dict[str, object]:
        """Convert to a plain, JSON-serializable dictionary with keys ``id``, ``name``,
        ``full_name``, ``regex``."""
        return {
            "id": str(self.id),
            "name": self.name,
            "full_name": self.full_name,
            "regex": self.regex,
        }
