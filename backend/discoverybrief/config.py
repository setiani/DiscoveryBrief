import os
from dataclasses import dataclass, field
from pathlib import Path


def load_dotenv(path: Path = Path(".env")) -> None:
    """Load simple KEY=value config without overriding explicit environment variables."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip().replace("_", "").isalnum():
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    mode: str
    research_mode: str
    data_dir: Path
    tavily_api_key: str = field(repr=False)
    bifrost_base_url: str
    bifrost_virtual_key: str = field(repr=False)
    model_primary: str
    model_fallback: str
    model_provider_base_url: str
    model_provider_api_key: str = field(repr=False)
    model_min_interval_seconds: float
    enable_live_tests: bool
    enable_live_runs: bool

    @classmethod
    def load(cls) -> "Settings":
        load_dotenv()
        return cls(
            mode=os.getenv("DISCOVERYBRIEF_MODE", "local"),
            research_mode=os.getenv("RESEARCH_MODE", "fixture"),
            data_dir=Path(os.getenv("APP_DATA_DIR", "./data")).resolve(),
            tavily_api_key=os.getenv("TAVILY_API_KEY", ""),
            bifrost_base_url=os.getenv(
                "BIFROST_BASE_URL", "http://127.0.0.1:8080/v1"
            ).rstrip("/"),
            bifrost_virtual_key=os.getenv("BIFROST_VIRTUAL_KEY", ""),
            model_primary=os.getenv("MODEL_PRIMARY", ""),
            model_fallback=os.getenv("MODEL_FALLBACK", ""),
            model_provider_base_url=os.getenv("MODEL_PROVIDER_BASE_URL", ""),
            model_provider_api_key=os.getenv("MODEL_PROVIDER_API_KEY", ""),
            model_min_interval_seconds=float(
                os.getenv("MODEL_MIN_INTERVAL_SECONDS", "15")
            ),
            enable_live_tests=os.getenv("ENABLE_LIVE_TESTS", "0") == "1",
            enable_live_runs=os.getenv("ENABLE_LIVE_RUNS", "0") == "1",
        )
