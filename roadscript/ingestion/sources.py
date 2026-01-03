"""Source definitions for INDOT document ingestion."""

from dataclasses import dataclass, field
import os
import re
from typing import List, Optional, Pattern


@dataclass(frozen=True)
class SourceConfig:
    """Configuration describing how to locate and download INDOT PDFs."""

    name: str
    index_url: str
    output_subdir: str
    include_keywords: List[str]
    index_include_keywords: List[str] = field(default_factory=list)
    exclude_keywords: List[str] = field(default_factory=list)
    index_exclude_keywords: List[str] = field(default_factory=list)
    link_regex: Optional[Pattern[str]] = None
    index_link_regex: Optional[Pattern[str]] = None
    download_mode: str = "latest"
    index_download_mode: str = "latest"


def _env_list(name: str, default: List[str]) -> List[str]:
    value = os.getenv(name)
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def get_sources() -> List[SourceConfig]:
    """Return default source configs with environment overrides."""
    spec_url = os.getenv(
        "INDOT_SPEC_URL",
        "https://www.in.gov/dot/div/contracts/standards/book/index.html",
    )
    idm_url = os.getenv(
        "INDOT_IDM_URL",
        "https://www.in.gov/dot/div/contracts/design/IDM.htm",
    )
    drawings_url = os.getenv(
        "INDOT_DRAWINGS_URL",
        "https://www.in.gov/dot/div/contracts/standards/drawings/index.html",
    )

    idm_mode = os.getenv("INDOT_IDM_MODE", "all")
    if idm_mode not in {"all", "latest"}:
        idm_mode = "all"

    return [
        SourceConfig(
            name="standard_specifications",
            index_url=spec_url,
            output_subdir="standard_specifications",
            include_keywords=_env_list(
                "INDOT_SPEC_KEYWORDS",
                ["standard specifications"],
            ),
            index_include_keywords=_env_list("INDOT_SPEC_INDEX_KEYWORDS", []),
            exclude_keywords=_env_list("INDOT_SPEC_EXCLUDE", ["changes", "revision"]),
            link_regex=re.compile(r".*specifications.*\.pdf$", re.IGNORECASE),
            index_link_regex=re.compile(r"sep\d{2}/sep\.htm[l]?$", re.IGNORECASE),
            download_mode="latest",
            index_download_mode="latest",
        ),
        SourceConfig(
            name="design_manual",
            index_url=idm_url,
            output_subdir="design_manual",
            include_keywords=_env_list("INDOT_IDM_KEYWORDS", []),
            exclude_keywords=_env_list("INDOT_IDM_EXCLUDE", ["portfolio"]),
            link_regex=re.compile(r".*\.pdf$", re.IGNORECASE),
            download_mode=idm_mode,
        ),
        SourceConfig(
            name="standard_drawings",
            index_url=drawings_url,
            output_subdir="standard_drawings",
            include_keywords=_env_list("INDOT_DRAWINGS_KEYWORDS", []),
            index_include_keywords=_env_list("INDOT_DRAWINGS_INDEX_KEYWORDS", []),
            exclude_keywords=_env_list(
                "INDOT_DRAWINGS_EXCLUDE",
                ["standard drawings effective", "std dwgs eff"],
            ),
            link_regex=re.compile(r".*\.pdf$", re.IGNORECASE),
            index_link_regex=re.compile(r"sep\d{2}/sep\.htm[l]?$", re.IGNORECASE),
            download_mode="all",
            index_download_mode="latest",
        ),
    ]
