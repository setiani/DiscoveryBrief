from datetime import UTC, datetime, timedelta
from ipaddress import ip_address
from typing import Literal
from unicodedata import normalize
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Participant(StrictModel):
    name: str = Field(min_length=1, max_length=100)
    role: str | None = Field(default=None, max_length=100)
    organization: str | None = Field(default=None, max_length=150)
    source_note: str | None = Field(default=None, max_length=200)


class RunRequest(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    client_request_id: UUID | None = None
    company_name: str = Field(min_length=2, max_length=160)
    company_domain: str | None = None
    company_country: str | None = Field(default=None, max_length=80)
    company_industry: str | None = Field(default=None, max_length=100)
    meeting_at: datetime
    meeting_timezone: str = "Asia/Jakarta"
    meeting_type: Literal["discovery", "rfp_clarification", "partnership"] = "discovery"
    meeting_goal: str = Field(default="", max_length=500)
    public_topics: list[
        Literal["portal", "integration", "identity", "search", "devops"]
    ] = Field(default_factory=list, max_length=3)
    participants: list[Participant] = Field(default_factory=list, max_length=6)
    rfp_text: str = Field(default="", max_length=12000)
    notes: str = Field(default="", max_length=4000)
    language: Literal["id", "en"] = "id"

    @field_validator("rfp_text", "notes", mode="before")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        return normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))

    @field_validator("company_domain")
    @classmethod
    def domain_is_hostname(cls, value: str | None) -> str | None:
        if not value:
            return None
        import re

        domain = value.lower().rstrip(".")
        if len(domain) > 253 or not re.fullmatch(
            r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", domain
        ):
            raise ValueError(
                "domain must be a public hostname without URL, port or path"
            )
        if "." not in domain or any(
            not part or len(part) > 63 or part.startswith("-") or part.endswith("-")
            for part in domain.split(".")
        ):
            raise ValueError("invalid hostname")
        if domain.endswith((".local", ".internal", ".localhost")):
            raise ValueError("private hostname is not allowed")
        try:
            ip_address(domain)
        except ValueError:
            return domain
        raise ValueError("IP addresses are not allowed")

    @model_validator(mode="after")
    def valid_zone(self) -> "RunRequest":
        if self.meeting_at.utcoffset() is None:
            raise ValueError("meeting_at must include a timezone offset")
        try:
            expected_offset = self.meeting_at.astimezone(
                ZoneInfo(self.meeting_timezone)
            ).utcoffset()
        except ZoneInfoNotFoundError as exc:
            raise ValueError("unknown IANA timezone") from exc
        if self.meeting_at.utcoffset() != expected_offset:
            raise ValueError("meeting_at offset does not match meeting_timezone")
        return self

    def validate_horizon(self, now: datetime) -> None:
        if now.utcoffset() is None:
            raise ValueError("clock must be timezone-aware")
        now = now.astimezone(UTC)
        if not now - timedelta(hours=24) <= self.meeting_at <= now + timedelta(days=30):
            raise ValueError("meeting must be within the past 24 hours or next 30 days")

    def public_context(self, created_at: datetime) -> dict:
        cutoff = min(created_at, self.meeting_at)
        return {
            "company_name": self.company_name,
            "company_domain": self.company_domain,
            "company_country": self.company_country,
            "company_industry": self.company_industry,
            "meeting_type": self.meeting_type,
            "public_topics": self.public_topics,
            "window_start": (self.meeting_at - timedelta(days=30)).isoformat(),
            "knowledge_cutoff": cutoff.isoformat(),
            "language": self.language,
        }
