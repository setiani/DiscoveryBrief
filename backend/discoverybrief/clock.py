from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


@dataclass(frozen=True)
class FrozenClock:
    instant: datetime

    def now(self) -> datetime:
        if self.instant.utcoffset() is None:
            raise ValueError("clock must be timezone-aware")
        return self.instant.astimezone(UTC)
